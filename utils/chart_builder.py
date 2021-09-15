import plotly.graph_objects as go


def create_horizontal_barchart(chart_data, chart_specs, **kwargs):
    dict_of_fig = dict(
        {
            "data": {
                "type": "bar",
                "x": chart_data[chart_specs["value"]],
                "y": chart_data[chart_specs["label"]],
                "text": chart_data[chart_specs["value"]],
                "textposition": "outside",
                "orientation": "h",
                "meta": chart_specs["meta_template"].format(**kwargs["meta_variables"]),
                "hovertemplate": chart_specs["hovertemplate"],
                "opacity": 0.9,
                "marker_line": {"color": "white", "width": 1},
            },
            "layout": {
                "yaxis": {"categoryorder": "total ascending"},
                "xaxis": {
                    "zeroline": True,
                    "zerolinewidth": 1,
                    "zerolinecolor": "black",
                    "gridcolor": "black",
                },
                "title": {
                    "text": chart_specs["chart_title"].format(
                        **kwargs["title_wildcards"]
                    ),
                    "y": 0.9,
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                    "font": {"size": 24},
                },
                "paper_bgcolor": "rgba(162,162,162,0.1)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "margin_pad": 10,
            },
        }
    )
    if "marker_color_list" in chart_specs:
        dict_of_fig["data"]["marker_color"] = chart_specs["marker_color_list"]
    if "color_col" in chart_specs:
        dict_of_fig["data"]["marker"] = {
            "color": chart_data[chart_specs["color_col"]],
            "colorscale": chart_specs["colorscale"],
        }
    fig = go.Figure(dict_of_fig)
    return fig
