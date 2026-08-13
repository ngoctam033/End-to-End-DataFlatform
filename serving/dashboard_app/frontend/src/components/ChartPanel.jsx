import { useEffect, useRef } from "react";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { Panel } from "./Panel";

echarts.use([BarChart, CanvasRenderer, GridComponent, LegendComponent, LineChart, PieChart, TooltipComponent]);

export function ChartPanel({ title, meta, wide = false, option }) {
  const chartRef = useRef(null);
  const instanceRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current) {
      return undefined;
    }

    instanceRef.current = echarts.init(chartRef.current);

    const resizeObserver = new ResizeObserver(() => {
      instanceRef.current?.resize();
    });

    resizeObserver.observe(chartRef.current);

    return () => {
      resizeObserver.disconnect();
      instanceRef.current?.dispose();
      instanceRef.current = null;
    };
  }, []);

  useEffect(() => {
    instanceRef.current?.setOption(option, true);
  }, [option]);

  return (
    <Panel title={title} meta={meta} wide={wide}>
      <div ref={chartRef} className="chart" />
    </Panel>
  );
}
