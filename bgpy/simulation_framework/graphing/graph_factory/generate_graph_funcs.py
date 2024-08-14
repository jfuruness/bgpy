from dataclasses import replace
from typing import TYPE_CHECKING

from frozendict import frozendict

from ..line_data import LineData
from ..line_info import LineInfo

if TYPE_CHECKING:
    from bgpy.simulation_framework import GraphCategory, DataPointKey, DataPointAggData


def _generate_graph(
    self,
    graph_category: "GraphCategory",
    data_dict: dict["DataPointKey", "DataPointAggData"],
) -> None:
    """Writes a graph to the graph dir"""

    if not data_dict:
        return

    graph_name, line_data_dict, fig, ax = self._preprocessing_steps(
        graph_category, data_dict
    )

    (
        non_aggregated_data_dict,
        max_attacker_data_dict,
    ) = self._graph_data(ax, line_data_dict)

    self._add_legends_and_save(
        fig,
        ax,
        graph_category,
        non_aggregated_data_dict,
        max_attacker_data_dict,
        graph_name,
    )


def _graph_data(self, ax, line_data_dict: dict[str, LineData]):
    # Add all lines that aren't aggregated into a strongest attacker aggregation
    self._plot_non_aggregated_lines(ax, line_data_dict)

    (
        non_aggregated_line_data_dict,
        max_attacker_data_dict,
    ) = self._plot_strongest_attacker_lines(ax, line_data_dict)
    return non_aggregated_line_data_dict, max_attacker_data_dict


def _plot_non_aggregated_lines(self, ax, line_data_dict: dict[str, LineData]) -> None:
    """Add all lines that aren't aggregated into a strongest attacker aggregation"""

    for label, line_data in line_data_dict.items():
        # Labels to aggregate for the strongest attacker shouldn't be plotted
        if label not in self.labels_to_aggregate:
            self._plot_line_data(ax, line_data)


def _plot_strongest_attacker_lines(self, ax, line_data_dict: dict[str, LineData]):
    # Add all lines that are aggregated
    max_attacker_data_dict: dict[str, LineData] = {
        label: line_data_dict.pop(label) for label in self.labels_to_aggregate
    }

    if self.labels_to_aggregate:

        strongest_agg_dict, scatter_line_data_dict = self._get_agg_data(
            max_attacker_data_dict
        )

        agg_line_datas = self._get_agg_line_data(strongest_agg_dict)

        for agg_line_data in agg_line_datas:
            line_data_dict[agg_line_data.label] = agg_line_data
            self._plot_line_data(ax, agg_line_data)

        self._plot_scatter_plots(ax, scatter_line_data_dict)

    return line_data_dict, max_attacker_data_dict


def _get_agg_data(self, max_attacker_data_dict):
    # Gets all lines that will be in the scatter plot
    # So basically each line beforehand, but some X values will
    # be removed if they aren't the strongest listed
    scatter_plots: dict[str, dict[str, list[float]]] = {  # type: ignore
        label: {"xs": [], "ys": [], "yerrs": []}
        for label in self.labels_to_aggregate
    }

    # Get all strongest attacker lines. No data point markers, but the
    # line itself that will be plotted
    agg_xs = list(max_attacker_data_dict.values())[0].xs
    strongest_agg_dict: dict[str, dict[str, list[float]]] = {  # type: ignore
        label: {"agg_xs": agg_xs, "agg_ys": [], "agg_yerrs": [0 for _ in agg_xs]}
        for label in self.strongest_attacker_dict
    }


    # Populate the new agg line and scatter plots
    for strongest_attacker_label, labels_to_agg in self.strongest_attacker_dict.items():
        # {agg_xs, agg_ys, agg_yerrs}
        cur_data = strongest_agg_dict[strongest_attacker_label]

        for i, x in enumerate(cur_data["agg_xs"]):
            best_label = None
            max_val = None
            new_yerr = None
            for label in labels_to_agg:
                line_data = max_attacker_data_dict[label]
                if max_val is None or line_data.ys[i] > max_val:  # type: ignore
                    best_label = label
                    max_val = line_data.ys[i]
                    new_yerr = line_data.yerrs[i]
            cur_data["agg_ys"].append(max_val)
            assert isinstance(best_label, str), "For mypy"
            assert isinstance(max_val, float), "For mypy"
            assert isinstance(new_yerr, float), "For mypy"
            scatter_plots[best_label]["xs"].append(x)
            scatter_plots[best_label]["ys"].append(max_val)
            scatter_plots[best_label]["yerrs"].append(new_yerr)

    scatter_line_data_dict = self._get_scatter_line_data_dict(
        scatter_plots, max_attacker_data_dict
    )
    return strongest_agg_dict, scatter_line_data_dict


def _get_scatter_line_data_dict(self, scatter_plots, max_attacker_dict):
    """Converts scatter plots into proper line data for plotting"""

    scatter_line_data_dict = dict()
    for label, point_dict in scatter_plots.items():
        old_line_data = max_attacker_dict[label]

        scatter_line_data_dict[label] = LineData(
            label=old_line_data.label,
            formatted_graph_rows=None,
            # This makes the line dissapear
            line_info=replace(
                old_line_data.line_info,
                ls="solid",
                color="grey",
                extra_kwargs={
                    **dict(old_line_data.line_info.extra_kwargs),
                    **{
                        # Marker face color
                        "mfc": old_line_data.line_info.color,
                        # Marker edge color
                        "mec": old_line_data.line_info.color,
                        # Marker size
                        "ms": 20,
                        "markeredgewidth": 3,
                        # Old line color
                        "ecolor": old_line_data.line_info.color,
                        "zorder": 3,
                    },
                },
            ),
            xs=point_dict["xs"],
            ys=point_dict["ys"],
            yerrs=point_dict["yerrs"],
        )
    return scatter_line_data_dict


def _get_agg_line_data(self, strongest_agg_dict) -> tuple[LineData, ...]:
    line_data = list()
    for agg_label, agg_data_dict in strongest_agg_dict.items():
        line_datas.append(
            LineData(
                agg_label,
                formatted_graph_rows=None,
                line_info=LineInfo(
                    agg_label,
                    marker=".",
                    ls="solid",
                    color="gray",
                    # Ms stands for marker size
                    extra_kwargs=frozendict({"zorder": 0, "ms": 0, "elinewidth": 0}),
                ),
                xs=agg_data_dict["agg_xs"],
                ys=agg_data_dict["agg_ys"],
                yerrs=agg_data_dict["agg_yerrs"],
            )
        )
    return tuple(line_data)


def _plot_line_data(self, ax, line_data: LineData):
    """Plots line data"""

    return ax.errorbar(
        line_data.xs,
        line_data.ys,
        line_data.yerrs,
        label=line_data.line_info.label,
        marker=line_data.line_info.marker,
        ls=line_data.line_info.ls,
        color=line_data.line_info.color,
        **line_data.line_info.extra_kwargs,
    )


def _plot_scatter_plots(self, ax, scatter_plot_line_data_dict):
    """Plots scatter plots"""

    for line_data in scatter_plot_line_data_dict.values():
        self._plot_line_data(ax, line_data)
