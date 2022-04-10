# # Run this app with `python app.py` and
# # visit http://127.0.0.1:8050/ in your web browser.
#
# from dash import Dash, html, dcc
# import plotly.express as px
# import pandas as pd
#
# app = Dash(__name__)
#
# # assume you have a "long-form" data frame
# # see https://plotly.com/python/px-arguments/ for more options
# df = pd.DataFrame({
#     "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
#     "Amount": [4, 1, 2, 2, 4, 5],
#     "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
# })
#
# fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")
#
# app.layout = html.Div(children=[
#     html.H1(children='Hello Dash'),
#
#     html.Div(children='''
#         Dash: A web application framework for your data.
#     '''),
#
#     dcc.Graph(
#         id='example-graph',
#         figure=fig
#     )
# ])
#
#
# from dash.exceptions import PreventUpdate
#
#
# @app.callback(
#     Output("graph", "figure"),
#     [Input("refresh-graph-interval", "n_intervals")]
# )
# def refresh_graph_interval_callback(n_intervals):
#     if n_intervals is not None:
#         for i in range(0,5):
#             time.sleep(0.1)
#             randomfunction(i)
#             return plot
#     raise PreventUpdate()
#
# import dash_core_components as dcc
# dcc.Interval(id="refresh-graph-interval", disabled=False, interval=1000)
#
#
# if __name__ == '__main__':
#     app.run_server(debug=True)
