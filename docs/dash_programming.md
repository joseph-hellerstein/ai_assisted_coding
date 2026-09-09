# Dash Programming

## What is Dash?

``Dash`` is a Python package for writing web applications that allows Python programmers to create web applications. The application can be deployed locally on the user's machine. Or, the application can be deployed on a separate server.

## Structure of a ``Dash`` application

### Widgets

**Widget** is the generic term for a elements of a GUI application, although not all widgets are visible. Examples of widgets are text entry boxes and dropdowns. Widgets typically have the following properties:

* *name*: a string used to reference the element
* *value*: typically something that is entered or displayed
* *type*: the kind of widget (e.g., butten, entry field)
* *children*: hierarchical relationship to other widgets

We can create very complex GUIs with widgets because they are hierarchical; that is, a widget can specify other widgets.

### Layout

Layout is is the manner in which widgets are organized on the screen. This organization can be dynamical in the sense that it changes as the user inputs information (e.g., with text and/or buttons). The layout is specified by the ``layout`` property. To create the layout, first create the ``Dash`` object, which takes a string argument of the application.

    app = Dash(__name__)

Next, use the ``Dash`` object to construct the layout.

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

## Widget Namespace

The term **namespace** refers to a set of interrelated names that are used to make references for reading and writing information. Widget names provide a namespace that is used to read and write information in ``Dash`` programming. Widgets can have *properties* that contain text, numbers, other widgets, and other kinds of objects. Properties can be named as well.

## Callbacks

Callbacks are a programming technique that connects the Python namespace (the Python variables that you program) with the Widget namespace. A callback is specified by a special function called a *decorator* that begins with an "at" sign ("@"). This illustrated below.

    @app.callback(
        Output("submit-output", "children"),
        Input("submit-button", "n_clicks"),
        State("state-input", "value"),
    )
    def handle_submit(n_clicks, text_value):
        if n_clicks == 0:
            return "Click Submit to see the text value."
        return f"Submitted (click #{n_clicks}): '{text_value}'"a

We see a specification of the callback followed by the definition of the function ``handle_submit``.

``@app.callback`` is a decorator that specifies the inputs to and outputs from ``handle_submit``. Here's how the callback and the function are connected. We consider each argument of the callback.

* ``Output("submit-output", "children")`` specifies the widget to which information is written (``submit-output``) along with where in the widget the information is placed (``children``).
* ``Input("submit-button", "n_clicks")`` specifies the value contained in the ``n_clicks`` property of the ``submit-button`` widget. An "Input" is available as soon as its value has changed.
* ``State`` provides input to ``handle_submit`` that is in the widget ``state-input``, its property ``value``. Like Input, State is an argument to a function. The one distinction is that a change in state does not cause the callback to execute. Only a change in Input causes the callback to execute.

## Running a ``Dash`` application

The ``Dash`` main program should have the following at the bottom of the file.

    if __name__ == "__main__":
        app.run()

To run in debug mode, include the keyword argument ``debug=True`` in the call to ``run``. ``Dash`` will display a URL where the web page can be found. Browse to that page to interact with your application.
