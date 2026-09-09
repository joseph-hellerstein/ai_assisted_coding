"""
Complete Dash app illustrating:
  - Basic Input/Output callbacks
  - Dynamic 'children' updates (text, components, and lists of components)
  - Using State alongside Input
  - A simple pattern-matching callback (ALL) for dynamically added items

Run with:
    pip install dash
    python app.py
Then open http://127.0.0.1:8050 in your browser.
"""

from dash import Dash, dcc, html, Input, Output, State, ALL, ctx, no_update
import plotly.express as px # type: ignore

app = Dash(__name__)

# --- Sample data for the graph example -------------------------------------
df = px.data.gapminder().query("year == 2007")

# --- Layout ------------------------------------------------------------------
app.layout = html.Div([

    html.H1("Dash Callback & 'children' Demo"),

    # --- Example 1: Simple text-in / text-out callback ---
    html.Hr(),
    html.H2("1. Basic text callback"),
    dcc.Input(id="name-input", value="", type="text", placeholder="Type your name..."),
    html.Div(id="greeting-output"),  # <- children of this Div will be updated

    # --- Example 2: Returning a whole component (e.g. a graph) as children ---
    html.Hr(),
    html.H2("2. Returning components as children"),
    dcc.Dropdown(
        id="content-dropdown",
        options=[
            {"label": "Show a graph", "value": "graph"},
            {"label": "Show a table", "value": "table"},
            {"label": "Show nothing", "value": "none"},
        ],
        value="none",
        clearable=False,
    ),
    html.Div(id="dynamic-content"),  # <- entire component tree gets swapped in here

    # --- Example 3: Input vs State (only react on button click) ---
    html.Hr(),
    html.H2("3. Input vs State"),
    dcc.Input(id="state-input", type="text", placeholder="Won't fire until you click Submit"),
    html.Button("Submit", id="submit-button", n_clicks=0),
    html.Div(id="submit-output"),

    # --- Example 4: Dynamically growing list of children (pattern-matching) ---
    html.Hr(),
    html.H2("4. Dynamic list of children (pattern-matching callback)"),
    html.Button("Add item", id="add-item-button", n_clicks=0),
    html.Div(id="item-list", children=[]),  # children starts as an empty list
    html.Div(id="item-count-output"),

])


# =============================================================================
# Example 1: Basic Input -> Output, children as a string
# =============================================================================
@app.callback(
    Output("greeting-output", "children"),
    Input("name-input", "value"),
)
def update_greeting(name):
    if not name:
        return "Enter your name above."
    return f"Hello, {name}!"


# =============================================================================
# Example 2: children can be an entire component (or None)
# =============================================================================
@app.callback(
    Output("dynamic-content", "children"),
    Input("content-dropdown", "value"),
)
def update_dynamic_content(selection):
    if selection == "graph":
        fig = px.scatter(
            df, x="gdpPercap", y="lifeExp", size="pop", color="continent",
            hover_name="country", log_x=True, size_max=60,
            title="Life Expectancy vs GDP per Capita (2007)",
        )
        return dcc.Graph(figure=fig)

    elif selection == "table":
        # Return a list of children: a header row + a few data rows
        rows = [
            html.Tr([html.Th("Country"), html.Th("Continent"), html.Th("Population")])
        ]
        for _, row in df.head(5).iterrows():
            rows.append(
                html.Tr([
                    html.Td(row["country"]),
                    html.Td(row["continent"]),
                    html.Td(round(row["pop"], 1)),
                ])
            )
        return html.Table(rows)

    else:
        return html.P("Nothing selected.")


# =============================================================================
# Example 3: Input (n_clicks) vs State (text value)
#   - Typing in the text box does NOT trigger this callback
#   - Clicking the button does, and reads the current text via State
# =============================================================================
@app.callback(
    Output("submit-output", "children"),
    State("state-input", "value"),
    Input("submit-button", "n_clicks"),
)
def handle_submit(text_value, n_clicks):
    if n_clicks == 0:
        return "Click Submit to see the text value."
    return f"Submitted (click #{n_clicks}): '{text_value}'"


# =============================================================================
# Example 4: Growing a list of children dynamically, plus a pattern-matching
# callback that reacts to ANY of the dynamically created "remove" buttons.
# =============================================================================
@app.callback(
    Output("item-list", "children"),
    Input("add-item-button", "n_clicks"),
    Input({"type": "remove-item-button", "index": ALL}, "n_clicks"),
    State("item-list", "children"),
    prevent_initial_call=True,
)
def modify_item_list(add_clicks, remove_clicks_list, current_children):
    triggered_id = ctx.triggered_id
    import pdb; pdb.set_trace()  # Debugging breakpoint

    # Case A: the "Add item" button was clicked -> append a new row
    if triggered_id == "add-item-button":
        new_index = len(current_children)
        new_row = html.Div(
            [
                html.Span(f"Item {new_index + 1}"),
                html.Button(
                    "Remove",
                    id={"type": "remove-item-button", "index": new_index},
                    n_clicks=0,
                    style={"marginLeft": "10px"},
                ),
            ],
            id={"type": "item-row", "index": new_index},
        )
        return current_children + [new_row]

    # Case B: one of the dynamically generated "Remove" buttons was clicked
    if isinstance(triggered_id, dict) and triggered_id.get("type") == "remove-item-button":
        removed_index = triggered_id["index"]
        # Filter out the row whose id matches the clicked remove button
        return [
            child for child in current_children
            if child["props"]["id"]["index"] != removed_index
        ]

    return no_update


@app.callback(
    Output("item-count-output", "children"),
    Input("item-list", "children"),
)
def update_item_count(children):
    return f"Current item count: {len(children)}"


if __name__ == "__main__":
    app.run(debug=True)