# Pair Finder Utility

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

Finds integer pairs `(x, y)` satisfying constraints derived from multipliers and a threshold, via an easy-to-use web interface.

## Description

This tool calculates integer pairs `(x, y)` that simultaneously satisfy a specific set of absolute value inequalities derived from user-provided multipliers `mx` (> 1) and `my` (> 1), subject to lower and upper bounds for `x` and `y`.

The core inequalities solved are:
*   `|(mx - 1) * x - y| <= T`
*   `|(my - 1) * y - x| <= T`
Where `T` is a given threshold value.

The underlying script determines pairs within the specified `X_MIN`/`X_MAX` and `Y_MIN`/`Y_MAX` bounds (defaults are 301 to 999 for both).

## Features

*   **Web Interface:** Easy-to-use online application - no installation required!
*   Accepts user-defined multipliers `mx` and `my` (must be > 1).
*   Accepts a specific non-negative integer threshold `T`.
*   Alternatively, allows automatic calculation of the *minimum possible integer threshold* `T` that yields at least one solution (option 'm' in the original script, now a radio button).
*   Configurable bounds and display count *within the source code* for potential modification.
*   **Representative Sampling:** If the total number of valid pairs is large, the app displays a sample distributed across the range of `x` values, rather than just the first few.

## How to Use (Web App)

This tool is designed to be run directly in your web browser via the deployed Streamlit application.

➡️ **Launch the Pair Finder App:** [**https://pairfindersak.streamlit.app/**](https://pairfindersak.streamlit.app/)

1.  **Open the Link:** Click the link above to open the application.
2.  **Enter Inputs:** Use the sidebar on the left:
    *   Enter your desired **Multiplier for x (`mx`)**.
    *   Enter your desired **Multiplier for y (`my`)**.
    *   Choose a **Threshold Option**:
        *   "Specify Threshold": Enter a whole number for `T`.
        *   "Calculate Minimum": Let the app find the smallest `T` (this can take time).
3.  **Calculate:** Click the **"Calculate Pairs"** button.
4.  **View Results:** The results, including the total pair count and a table of sampled/all pairs (up to 50), will appear in the main area of the page.


### Alternative approach
1. Install the requirements
   ```
   $ pip install -r requirements.txt
   ```
2. Run the app
   ```
   $ streamlit run streamlit_app.py
   ```

## Understanding the Output

*   **`Using derived coefficients...`**: Shows the `mx - 1` and `my - 1` values used.
*   **`Using specified/Minimum threshold...`**: Confirms the `T` value used.
*   **Status Messages:** Spinners and info boxes show calculation progress.
*   **`Total Pairs Found`**: A metric displaying the total count of pairs satisfying all conditions.
*   **`Displaying X pairs (Sampled/All)`**: Introduces the results table. "(Sampled)" appears if the total count exceeds the display limit (default 50).
*   **Results Table:** A table showing the calculated `(x, y)` pairs.

## Customization (Code Level)

While the web app is ready to use, the underlying Python script (`app.py` or `pair_finder.py` in this repository) contains default configurations that could be modified if you were forking or running the code yourself:

```python
# --- Configuration ---
X_MIN = 301 # Minimum allowed value for x
Y_MIN = 301 # Minimum allowed value for y
X_MAX = 999 # Maximum allowed value for x
Y_MAX = 999 # Maximum allowed value for y
NUM_PAIRS_TARGET = 50 # Max number of pairs to display

```

* Bounds: `X_MIN`, `Y_MIN`, `X_MAX`, `Y_MAX` define the search range.
* Display Count: `NUM_PAIRS_TARGET` sets the limit for displayed pairs before sampling occurs.


## License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0). Please see the LICENSE file for details.
