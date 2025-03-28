import streamlit as st
import pandas as pd
import math
import sys
import time

# --- Configuration (Defaults can be adjusted here) ---
DEFAULT_MX = 1.65
DEFAULT_MY = 2.0
DEFAULT_THRESHOLD = 70
DEFAULT_THRESHOLD_OPTION = "Specify Threshold" # "Specify Threshold" or "Calculate Minimum"

X_MIN = 301
Y_MIN = 301
X_MAX = 999
Y_MAX = 999
NUM_PAIRS_TARGET = 50 # Target number of pairs to display/sample

# --- Core Calculation Functions (CORRECTED) ---

# Note: Removed leading underscores from arguments for clarity and consistency.
# Using @st.cache_data should be safe here as long as X_MIN, Y_MIN etc. are treated as constant.
# If those were dynamic inputs, caching would need careful keys or removal.
@st.cache_data
def calculate_bounds(x_val, coeff_x, coeff_y, T_val):
    """Calculates the theoretical min/max y for a given x, T."""
    if coeff_y == 0:
        st.error("Error: Derived coefficient for y (my - 1) cannot be zero.")
        return None, None # Indicate error

    y_lower_1 = coeff_x * x_val - T_val
    y_upper_1 = coeff_x * x_val + T_val
    y_lower_2 = (x_val - T_val) / coeff_y
    y_upper_2 = (x_val + T_val) / coeff_y

    y_lower_theory = max(y_lower_1, y_lower_2)
    y_upper_theory = min(y_upper_1, y_upper_2)

    return y_lower_theory, y_upper_theory

# Minimum T calculation can be slow, so caching is less useful if run rarely,
# but keep the function definition clean.
# @st.cache_data # Removed cache for min T calculation - inputs are few, but run might be long
def find_minimum_threshold(coeff_x, coeff_y):
    """Finds the smallest integer T >= 1 that allows at least one (x,y) pair."""
    T = 1
    start_time = time.time()
    status_placeholder = st.empty() # Use a placeholder for status updates

    while True:
        status_placeholder.info(f"Calculating minimum threshold... Checking T = {T}")

        denominator = (1 - coeff_y * coeff_x)
        x_check_max = X_MAX # Default assumption
        valid_x_range_exists = True

        if denominator > 0:
            x_limit_theory = T * (1 + coeff_y) / denominator
            x_check_max = min(X_MAX, math.floor(x_limit_theory))
            if x_check_max < X_MIN:
                valid_x_range_exists = False
        elif denominator == 0:
            if T * (1 + coeff_y) < 0: valid_x_range_exists = False
        else: # denominator < 0
            x_lower_limit_theory = T * (1 + coeff_y) / denominator
            if x_lower_limit_theory > X_MAX: valid_x_range_exists = False
            st.warning(f"Warning: Denominator (1-coeff_y*coeff_x) = {denominator:.4f}. Min threshold logic might need review.")

        if not valid_x_range_exists:
            T += 1
            # Safety Break 1: If T gets unreasonably large relative to simple limits
            if T > (X_MAX + Y_MAX) * 2 :
                 status_placeholder.error("Error: Minimum threshold calculation aborted (T exceeded safety limit). Check multipliers/constraints.")
                 return None
            continue # Try next T

        found_pair_for_T = False
        current_x_min = X_MIN
        current_x_max = x_check_max

        for x in range(current_x_min, current_x_max + 1):
            # *** FIX: Pass the correct arguments to the corrected function ***
            bounds = calculate_bounds(x, coeff_x, coeff_y, T)
            if bounds == (None, None): # Check error return explicitly
                status_placeholder.error("Error during bounds calculation.")
                return None # Propagate error

            y_lower_theory, y_upper_theory = bounds
            y_check_min = math.ceil(y_lower_theory)
            y_check_max = math.floor(y_upper_theory)
            actual_y_min = max(Y_MIN, y_check_min)
            actual_y_max = min(Y_MAX, y_check_max)

            if actual_y_min <= actual_y_max:
                found_pair_for_T = True
                break # Found at least one pair for this T

        if found_pair_for_T:
            end_time = time.time()
            status_placeholder.success(f"Minimum threshold calculated: T = {T} (took {end_time - start_time:.2f}s)")
            return T

        T += 1
        # Safety Break 2: Duplicate check, maybe make limit slightly different?
        if T > (X_MAX + Y_MAX) * 2: # Keep safety break consistent
             status_placeholder.error("Error: Minimum threshold calculation aborted (T exceeded safety limit). Check multipliers/constraints.")
             return None

    # return None # This line should ideally not be reached due to breaks


@st.cache_data # Caching results for finding pairs is useful
def find_pairs_with_sampling(coeff_x, coeff_y, T_val, limit):
    """
    Finds pairs, sampling representatively if total exceeds limit.
    Returns (list_of_pairs, total_count)
    """
    pairs_found_sampled = []
    total_pairs_count = 0
    status_placeholder = st.empty() # Placeholder for status messages

    status_placeholder.info("Analyzing solution space and counting total pairs...")
    start_time_count = time.time()

    denominator = (1 - coeff_y * coeff_x)
    x_loop_max = X_MAX # Default
    valid_x_range_exists = True

    if denominator > 0:
        x_limit_theory = T_val * (1 + coeff_y) / denominator
        x_loop_max = min(X_MAX, math.floor(x_limit_theory))
        if x_loop_max < X_MIN: valid_x_range_exists = False
    elif denominator == 0:
        if T_val * (1 + coeff_y) < 0: valid_x_range_exists = False
    else: # denominator < 0
        x_lower_limit_theory = T_val * (1 + coeff_y) / denominator
        if x_lower_limit_theory > X_MAX: valid_x_range_exists = False
        st.warning(f"Warning: Denominator (1-coeff_y*coeff_x) = {denominator:.4f}. Pair finding logic might behave unexpectedly.")

    if not valid_x_range_exists:
        status_placeholder.warning("No valid x-range possible based on theoretical maximum for the given T.")
        return [], 0

    # --- Pass 1: Count ---
    count_status_every = max(1, (x_loop_max - X_MIN + 1) // 20) # Update status ~20 times during count
    for x in range(X_MIN, x_loop_max + 1):
        # *** FIX: Pass the correct arguments to the corrected function ***
        bounds = calculate_bounds(x, coeff_x, coeff_y, T_val)
        if bounds == (None, None): continue # Skip if error in bounds

        y_lower_theory, y_upper_theory = bounds
        y_check_min = math.ceil(y_lower_theory)
        y_check_max = math.floor(y_upper_theory)
        actual_y_min = max(Y_MIN, y_check_min)
        actual_y_max = min(Y_MAX, y_check_max)

        if actual_y_min <= actual_y_max:
            total_pairs_count += (actual_y_max - actual_y_min + 1)

        # Update status less frequently
        if (x - X_MIN) % count_status_every == 0:
             status_placeholder.info(f"Counting total pairs... Checking x ≈ {x}")

    end_time_count = time.time()
    status_placeholder.info(f"Count complete. Found {total_pairs_count:,} total valid pairs (count took {end_time_count - start_time_count:.2f}s).")

    if total_pairs_count == 0:
        return [], 0

    # --- Pass 2: Collect/Sample ---
    if total_pairs_count == 0: return [], 0

    pairs_collected = []
    sampling_needed = total_pairs_count > limit

    collect_status_message = "Collecting pairs (sampling if needed)..." if sampling_needed else "Collecting all pairs..."
    status_placeholder.info(collect_status_message)
    start_time_collect = time.time()
    pairs_seen = 0
    pairs_kept_count = 0

    collect_status_every = max(1, (x_loop_max - X_MIN + 1) // 20) # Similar status update frequency

    for x in range(X_MIN, x_loop_max + 1):
        # Update status less frequently
        if (x - X_MIN) % collect_status_every == 0:
             status_placeholder.info(f"{collect_status_message} Processing x ≈ {x}")

        # *** FIX: Pass the correct arguments to the corrected function ***
        bounds = calculate_bounds(x, coeff_x, coeff_y, T_val)
        if bounds == (None, None): continue # Skip if error in bounds

        y_lower_theory, y_upper_theory = bounds
        y_check_min = math.ceil(y_lower_theory)
        y_check_max = math.floor(y_upper_theory)
        actual_y_min = max(Y_MIN, y_check_min)
        actual_y_max = min(Y_MAX, y_check_max)

        if actual_y_min <= actual_y_max:
            for y in range(actual_y_min, actual_y_max + 1):
                if not sampling_needed:
                    pairs_collected.append((x, y))
                else:
                    pairs_seen += 1
                    target_kept_ideal = pairs_seen * limit / total_pairs_count
                    prev_target_kept_ideal = (pairs_seen - 1) * limit / total_pairs_count
                    if math.floor(target_kept_ideal) > math.floor(prev_target_kept_ideal) or pairs_seen == 1:
                        if pairs_kept_count < limit:
                            pairs_collected.append((x, y))
                            pairs_kept_count += 1

                # Optimization: Check break conditions less frequently? No, need precise check
                if sampling_needed and pairs_kept_count >= limit: break # Inner loop break
        if sampling_needed and pairs_kept_count >= limit: break # Outer loop break

    end_time_collect = time.time()
    # Final status update - clear the placeholder or show success
    status_placeholder.empty() # Remove the "Processing..." message

    # Only print timing if collection actually happened (not if total_pairs_count was 0)
    if total_pairs_count > 0:
        st.info(f"Collection/Sampling took {end_time_collect - start_time_collect:.2f}s.")

    return pairs_collected, total_pairs_count

# --- Streamlit UI (Largely the same, but uses corrected functions) ---

st.set_page_config(page_title="Pair Finder Utility", layout="wide")

st.title("🔢 Pair Finder Utility")
st.caption("Finds integer pairs (x, y) based on multiplier constraints and a threshold.")

# --- Inputs Sidebar ---
st.sidebar.header("Inputs")

mx = st.sidebar.number_input(
    "Multiplier for x (`mx`)",
    min_value=1.0001, # Must be > 1
    value=DEFAULT_MX,
    step=0.01,
    format="%.4f",
    help="Must be strictly greater than 1."
)

my = st.sidebar.number_input(
    "Multiplier for y (`my`)",
    min_value=1.0001, # Must be > 1
    value=DEFAULT_MY,
    step=0.01,
    format="%.4f",
    help="Must be strictly greater than 1."
)

threshold_option = st.sidebar.radio(
    "Threshold (`T`) Option",
    ("Specify Threshold", "Calculate Minimum"),
    index=("Specify Threshold", "Calculate Minimum").index(DEFAULT_THRESHOLD_OPTION), # Set default index
    help="Choose 'Calculate Minimum' to find the smallest T yielding solutions (can be slow)."
)

T_specified = None
if threshold_option == "Specify Threshold":
    T_specified = st.sidebar.number_input(
        "Threshold Value (`T`)",
        min_value=0,
        value=DEFAULT_THRESHOLD,
        step=1,
        help="Non-negative integer threshold."
    )

# --- Calculation Trigger ---
st.sidebar.markdown("---") # Separator
calculate_button = st.sidebar.button("📊 Calculate Pairs", use_container_width=True)
st.sidebar.markdown(f"*Displaying up to {NUM_PAIRS_TARGET} pairs.*")

# --- Main Area for Results ---
results_container = st.container() # Use a container for results

if calculate_button:
    with results_container: # Put results within the container
        st.subheader("Results")

        # Validate inputs
        valid_input = True
        if mx <= 1.0:
            st.error("Multiplier `mx` must be strictly greater than 1.")
            valid_input = False
        if my <= 1.0:
            st.error("Multiplier `my` must be strictly greater than 1.")
            valid_input = False
        if threshold_option == "Specify Threshold" and T_specified < 0:
            st.error("Specified Threshold `T` cannot be negative.")
            valid_input = False

        if valid_input:
            # Calculate coefficients
            coeff_x = mx - 1
            coeff_y = my - 1
            st.write(f"Using derived coefficients: `coeff_x = {coeff_x:.4f}`, `coeff_y = {coeff_y:.4f}`")

            # Determine T_actual
            T_actual = None
            if threshold_option == "Specify Threshold":
                T_actual = T_specified
                st.write(f"Using specified threshold: `T = {T_actual}`")
                # No need to call find_minimum_threshold
            else:
                # Calculate minimum T using the corrected function
                T_actual = find_minimum_threshold(coeff_x, coeff_y)
                # find_minimum_threshold now handles its own success/error messages
                if T_actual is None:
                    valid_input = False # Stop processing if min T failed

            # Proceed only if T_actual is determined
            if valid_input and T_actual is not None:
                # Find the pairs using corrected function
                result_pairs, total_count = find_pairs_with_sampling(coeff_x, coeff_y, T_actual, NUM_PAIRS_TARGET)

                # Display summary metric
                st.metric(label="Total Pairs Found", value=f"{total_count:,}")

                # Display the pairs
                if result_pairs:
                    sampling_info = "(Sampled)" if total_count > NUM_PAIRS_TARGET else "(All)"
                    st.write(f"Displaying **{len(result_pairs)}** pairs {sampling_info}:")
                    df_pairs = pd.DataFrame(result_pairs, columns=['x', 'y'])
                    df_pairs.index = df_pairs.index + 1
                    st.dataframe(df_pairs, use_container_width=True)

                elif total_count == 0: # Explicitly handle case where count is 0 after finding T
                     st.warning("No pairs found satisfying all conditions for this threshold.")

# --- Documentation Expanders (Keep as before) ---
st.markdown("---") # Separator
st.header("Documentation & Details")

with st.expander("About This App & Background"):
    st.markdown("""
    This application finds integer pairs `(x, y)` that satisfy specific absolute value inequalities derived from multipliers, within defined bounds.

    **Core Problem:**
    Given multipliers `mx > 1`, `my > 1`, and threshold `T >= 0`, find `(x, y)` such that:
    1.  `|(mx - 1) * x - y| <= T`
    2.  `|(my - 1) * y - x| <= T`
    3.  `{X_MIN} <= x <= {X_MAX}`
    4.  `{Y_MIN} <= y <= {Y_MAX}`

    **Development Journey:**
    This script originated from a specific need I identified. The process involved:
    1.  Starting with linear inequalities and realizing absolute values were needed.
    2.  Generalizing specific coefficients (like 0.65, 1) back to their multiplier origins (`mx=1.65`, `my=2`).
    3.  Implementing the 'minimum threshold' calculation based on exploring boundary conditions.
    4.  Automating the process into a command-line script.
    5.  Adding representative sampling to handle cases with thousands of results.
    6.  Creating this Streamlit interface for ease of use.
    *(Process facilitated via conversation with Google AI)*
    """, unsafe_allow_html=True) # Use markdown basic formatting

with st.expander("Mathematical Model Explained"):
    st.markdown(f"""
    Understanding the math helps interpret the results.

    **1. Core Inequalities:**
    From the multiplier formulation `|(mx*x - x) - y| <= T` and `|(my*y - y) - x| <= T`, we get:
    *   Let `coeff_x = mx - 1`
    *   Let `coeff_y = my - 1`
    *   Inequalities: `|coeff_x * x - y| <= T` and `|coeff_y * y - x| <= T`

    *(Example: If `mx=1.65`, `my=2`, then `coeff_x=0.65`, `coeff_y=1`, giving `|0.65x - y| <= T` and `|y - x| <= T`)*

    **2. Expanding Absolute Values:**
    *   `coeff_x * x - T <= y <= coeff_x * x + T`
    *   `(x - T) / coeff_y <= y <= (x + T) / coeff_y` (assuming `coeff_y > 0`)

    **3. Combined `y` Bounds:**
    `y` must be within the intersection:
    `max(coeff_x*x - T, (x-T)/coeff_y) <= y <= min(coeff_x*x + T, (x+T)/coeff_y)`

    **4. Constraint on `x` (Existence):**
    For solutions to exist, the lower `y` bound must be <= upper `y` bound. A necessary condition often leads to an upper limit on `x` based on `T` and the coefficients. For example, under certain conditions:
    `x <= T * (1 + coeff_y) / (1 - coeff_x * coeff_y)`
    *This explains why results might be limited to a certain `x` range for a given `T`.*

    **5. Integer & Boundary Constraints:**
    The final range for integer `y` is found by taking `ceil` of the lower bound, `floor` of the upper bound, and intersecting with the `[{Y_MIN}, {Y_MAX}]` range.
    """, unsafe_allow_html=True)

with st.expander("How to Use This Web App"):
     st.markdown(f"""
     1.  **Enter Multipliers:** Use the number inputs in the sidebar for `mx` and `my` (must be > 1).
     2.  **Choose Threshold Option:**
         *   Select "Specify Threshold" and enter a non-negative integer `T`.
         *   Select "Calculate Minimum" for the app to find the smallest `T` that works (can be slow).
     3.  **Click Calculate:** Press the 'Calculate Pairs' button in the sidebar.
     4.  **View Results:** The main area will show:
         *   The coefficients and threshold used.
         *   A metric showing the *total* number of valid pairs found.
         *   A table displaying up to **{NUM_PAIRS_TARGET}** pairs. If more pairs exist than the target, the displayed list is a representative sample.
     """)

with st.expander("Configuration & Customization (Code Level)"):
    st.markdown(f"""
    While this web app provides inputs, the underlying script has default bounds and display targets that can be changed by editing the Python code directly if needed (e.g., for local execution or if modifying the deployed app):

    ```python
    # --- Configuration ---
    X_MIN = {X_MIN} # Minimum allowed value for x
    Y_MIN = {Y_MIN} # Minimum allowed value for y
    X_MAX = {X_MAX} # Maximum allowed value for x
    Y_MAX = {Y_MAX} # Maximum allowed value for y
    NUM_PAIRS_TARGET = {NUM_PAIRS_TARGET} # Max # of pairs to display
    ```
    """)

with st.expander("License (CC BY-NC-SA 4.0)"):
    st.markdown("""
    This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License**.

    **You are free to:**
    *   **Share** — copy and redistribute the material in any medium or format.
    *   **Adapt** — remix, transform, and build upon the material.

    **Under the following terms:**
    *   **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made.
    *   **NonCommercial** — You may **not** use the material for commercial purposes.
    *   **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

    [Link to Full License](https://creativecommons.org/licenses/by-nc-sa/4.0/)
    """)

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.info("S.A.K")
