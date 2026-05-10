const chartNode = document.querySelector("#age-chart");
const sexFilter = document.querySelector("#sex-filter");

const margin = { top: 30, right: 24, bottom: 48, left: 56 };
const width = 760;
const height = 360;
let records = [];

const svg = d3
  .select(chartNode)
  .append("svg")
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("role", "img");

const chart = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
const innerWidth = width - margin.left - margin.right;
const innerHeight = height - margin.top - margin.bottom;

const x = d3.scaleBand().range([0, innerWidth]).padding(0.16);
const y = d3.scaleLinear().range([innerHeight, 0]);
const histogram = d3
  .bin()
  .value((record) => record.age)
  .domain([0, 100])
  .thresholds(d3.range(0, 101, 10));

const xAxis = chart.append("g").attr("transform", `translate(0,${innerHeight})`);
const yAxis = chart.append("g");
const title = svg.append("text").attr("x", margin.left).attr("y", 18).attr("class", "chart-title");
const tooltip = d3.select("body").append("div").attr("class", "chart-tooltip").style("display", "none");
const emptyText = chart
  .append("text")
  .attr("x", innerWidth / 2)
  .attr("y", innerHeight / 2)
  .attr("text-anchor", "middle")
  .attr("class", "text-secondary")
  .style("display", "none")
  .text("No records match the selected filters.");

async function loadChart() {
  const url = new URL(chartNode.dataset.url, window.location.origin);
  const response = await fetch(url);
  if (!response.ok) throw new Error("Unable to load analytics data.");
  const payload = await response.json();
  records = payload.records;
  render();
}

function filteredRecords() {
  return records.filter((record) => {
    return !sexFilter.value || record.sex === sexFilter.value;
  });
}

function render() {
  const selectedRecords = filteredRecords();
  const bins = histogram(selectedRecords).map((bin) => ({
    label: bin.x1 >= 100 ? "100+" : `${bin.x0}-${bin.x1 - 1}`,
    count: bin.length,
    percent: selectedRecords.length ? bin.length / selectedRecords.length : 0,
  }));

  x.domain(bins.map((item) => item.label));
  y.domain([0, Math.max(1, d3.max(bins, (item) => item.count))]).nice();

  title.text(`Patient age distribution (${selectedRecords.length} patients)`);
  emptyText.style("display", selectedRecords.length === 0 ? "block" : "none");

  xAxis.call(d3.axisBottom(x));
  yAxis.call(d3.axisLeft(y).ticks(5).tickFormat(d3.format("d")));

  const bars = chart.selectAll(".bar").data(bins, (item) => item.label);

  bars
    .join(
      (enter) =>
        enter
          .append("rect")
          .attr("class", "bar")
          .attr("x", (item) => x(item.label))
          .attr("width", x.bandwidth())
          .attr("y", innerHeight)
          .attr("height", 0),
      (update) => update,
      (exit) => exit.remove(),
    )
    .on("mousemove", (event, item) => {
      tooltip
        .style("display", "block")
        .style("left", `${event.pageX + 12}px`)
        .style("top", `${event.pageY - 24}px`)
        .text(`${item.count} patients (${d3.format(".1%")(item.percent)})`);
    })
    .on("mouseout", () => tooltip.style("display", "none"))
    .transition()
    .duration(180)
    .attr("x", (item) => x(item.label))
    .attr("width", x.bandwidth())
    .attr("y", (item) => y(item.count))
    .attr("height", (item) => innerHeight - y(item.count));

  const labels = chart.selectAll(".bar-label").data(bins, (item) => item.label);

  labels
    .join(
      (enter) =>
        enter
          .append("text")
          .attr("class", "bar-label")
          .attr("text-anchor", "middle")
          .attr("x", (item) => x(item.label) + x.bandwidth() / 2)
          .attr("y", (item) => y(item.count) - 6),
      (update) => update,
      (exit) => exit.remove(),
    )
    .text((item) => item.count)
    .transition()
    .duration(180)
    .attr("x", (item) => x(item.label) + x.bandwidth() / 2)
    .attr("y", (item) => y(item.count) - 6);
}

sexFilter.addEventListener("change", render);
loadChart();
