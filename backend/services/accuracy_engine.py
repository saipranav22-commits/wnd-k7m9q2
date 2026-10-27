import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.services.point_in_time import PointInTimeEngine
from backend.config import DEFAULT_DECISION_START_DATE, DEFAULT_DECISION_END_DATE, DEFAULT_DECISION_CUTOFF_TIME

logger = logging.getLogger(__name__)

class AccuracyEngine:
    def __init__(self, db: Session):
        self.db = db
        self.pit_engine = PointInTimeEngine(db)

    def calculate_metrics_for_pairs(self, pairs: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Takes list of dicts with 'forecast' and 'actual' (in MW).
        Returns calculated metrics.
        """
        valid_pairs = [p for p in pairs if p.get("forecast") is not None and p.get("actual") is not None]
        N = len(valid_pairs)
        if N == 0:
            return {
                "sample_count": 0,
                "mae_mw": 0.0,
                "rmse_mw": 0.0,
                "bias_mw": 0.0,
                "wape_percent": 0.0,
                "overforecast_count": 0,
                "underforecast_count": 0,
                "overforecast_rate_percent": 0.0,
                "underforecast_rate_percent": 0.0,
                "total_actual_mwh": 0.0,
                "total_forecast_mwh": 0.0,
                "average_actual_mw": 0.0,
                "average_forecast_mw": 0.0,
                "quantiles": {"p10": 0.0, "p25": 0.0, "p50_median": 0.0, "p75": 0.0, "p90": 0.0},
            }

        forecasts = np.array([p["forecast"] for p in valid_pairs], dtype=float)
        actuals = np.array([p["actual"] for p in valid_pairs], dtype=float)

        errors = forecasts - actuals  # signed error (MW)
        abs_errors = np.abs(errors)

        mae = float(np.mean(abs_errors))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        bias = float(np.mean(errors))

        sum_actuals = float(np.sum(actuals))
        sum_abs_errors = float(np.sum(abs_errors))
        wape = (sum_abs_errors / sum_actuals * 100.0) if sum_actuals > 0 else 0.0

        overforecast_count = int(np.sum(errors > 0.01))
        underforecast_count = int(np.sum(errors < -0.01))

        # Quantiles of signed errors
        q10, q25, q50, q75, q90 = np.percentile(errors, [10, 25, 50, 75, 90])

        return {
            "sample_count": N,
            "mae_mw": round(mae, 2),
            "rmse_mw": round(rmse, 2),
            "bias_mw": round(bias, 2),
            "wape_percent": round(wape, 2),
            "overforecast_count": overforecast_count,
            "underforecast_count": underforecast_count,
            "overforecast_rate_percent": round(overforecast_count / N * 100.0, 1),
            "underforecast_rate_percent": round(underforecast_count / N * 100.0, 1),
            "total_actual_mwh": round(sum_actuals, 2),
            "total_forecast_mwh": round(float(np.sum(forecasts)), 2),
            "average_actual_mw": round(float(np.mean(actuals)), 2),
            "average_forecast_mw": round(float(np.mean(forecasts)), 2),
            "quantiles": {
                "p10": round(float(q10), 2),
                "p25": round(float(q25), 2),
                "p50_median": round(float(q50), 2),
                "p75": round(float(q75), 2),
                "p90": round(float(q90), 2),
            },
        }

    def evaluate_month_accuracy(
        self,
        date_from_str: str = DEFAULT_DECISION_START_DATE,
        date_to_str: str = DEFAULT_DECISION_END_DATE,
        cutoff_time_str: str = DEFAULT_DECISION_CUTOFF_TIME,
    ) -> Dict[str, Any]:
        """
        Evaluate full multi-day accuracy over decisions from date_from to date_to.
        """
        d_start = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        d_end = datetime.strptime(date_to_str, "%Y-%m-%d").date()

        current_d = d_start
        all_pairs: List[Dict[str, Any]] = []
        daily_metrics: List[Dict[str, Any]] = []
        hourly_buckets: Dict[int, List[Dict[str, float]]] = {h: [] for h in range(24)}
        total_possible_slots = 0

        while current_d <= d_end:
            cur_str = current_d.strftime("%Y-%m-%d")
            res = self.pit_engine.get_day_ahead_matched_data(cur_str, cutoff_time_str)
            hourly_recs = res["hourly_records"]
            total_possible_slots += len(hourly_recs)

            day_pairs: List[Dict[str, float]] = []
            for r in hourly_recs:
                if r["forecast_mw"] is not None and r["actual_mw"] is not None:
                    pair = {
                        "forecast": r["forecast_mw"],
                        "actual": r["actual_mw"],
                        "start_time_utc": r["start_time_utc"],
                        "hour": r["hour"],
                        "delivery_date": res["delivery_date"],
                        "decision_date": cur_str,
                    }
                    all_pairs.append(pair)
                    day_pairs.append(pair)
                    hourly_buckets[r["hour"]].append({"forecast": r["forecast_mw"], "actual": r["actual_mw"]})

            day_calc = self.calculate_metrics_for_pairs(day_pairs)
            daily_metrics.append({
                "decision_date": cur_str,
                "delivery_date": res["delivery_date"],
                "sample_count": day_calc["sample_count"],
                "mae_mw": day_calc["mae_mw"],
                "rmse_mw": day_calc["rmse_mw"],
                "bias_mw": day_calc["bias_mw"],
                "wape_percent": day_calc["wape_percent"],
                "actual_mwh": day_calc["total_actual_mwh"],
                "forecast_mwh": day_calc["total_forecast_mwh"],
            })

            current_d += timedelta(days=1)

        overall = self.calculate_metrics_for_pairs(all_pairs)
        coverage_percent = round((overall["sample_count"] / total_possible_slots * 100.0), 1) if total_possible_slots > 0 else 0.0

        # Hourly metrics breakdown
        hourly_metrics: List[Dict[str, Any]] = []
        for h in range(24):
            h_calc = self.calculate_metrics_for_pairs(hourly_buckets[h])
            hourly_metrics.append({
                "hour": h,
                "sample_count": h_calc["sample_count"],
                "mae_mw": h_calc["mae_mw"],
                "rmse_mw": h_calc["rmse_mw"],
                "bias_mw": h_calc["bias_mw"],
                "actual_avg_mw": h_calc["average_actual_mw"],
                "forecast_avg_mw": h_calc["average_forecast_mw"],
            })

        # Error distribution histogram (20 bins)
        error_distribution = []
        scatter_points = []
        if all_pairs:
            errors = [p["forecast"] - p["actual"] for p in all_pairs]
            counts, bin_edges = np.histogram(errors, bins=20)
            for i in range(len(counts)):
                error_distribution.append({
                    "bin_min": round(float(bin_edges[i]), 1),
                    "bin_max": round(float(bin_edges[i+1]), 1),
                    "bin_center": round(float((bin_edges[i] + bin_edges[i+1]) / 2.0), 1),
                    "count": int(counts[i]),
                })
            # Subsample scatter points if large, up to 500 points
            stride = max(1, len(all_pairs) // 500)
            for p in all_pairs[::stride]:
                scatter_points.append({
                    "actual_mw": p["actual"],
                    "forecast_mw": p["forecast"],
                    "error_mw": round(p["forecast"] - p["actual"], 2),
                    "start_time_utc": p["start_time_utc"],
                })

        return {
            "date_from": date_from_str,
            "date_to": date_to_str,
            "cutoff_time": cutoff_time_str,
            "sample_count": overall["sample_count"],
            "coverage_percent": coverage_percent,
            "mae_mw": overall["mae_mw"],
            "rmse_mw": overall["rmse_mw"],
            "bias_mw": overall["bias_mw"],
            "wape_percent": overall["wape_percent"],
            "overforecast_count": overall["overforecast_count"],
            "underforecast_count": overall["underforecast_count"],
            "overforecast_rate_percent": overall["overforecast_rate_percent"],
            "underforecast_rate_percent": overall["underforecast_rate_percent"],
            "quantiles": overall["quantiles"],
            "daily_metrics": daily_metrics,
            "hourly_metrics": hourly_metrics,
            "error_distribution": error_distribution,
            "scatter_points": scatter_points,
        }

    def generate_commentary(self, kpis: Dict[str, Any], delivery_date_str: str) -> str:
        """
        Generate business-oriented analytical commentary for the utility's day-ahead desk.
        """
        bias = kpis.get("bias_mw", 0.0)
        mae = kpis.get("mae_mw", 0.0)
        wape = kpis.get("wape_percent", 0.0)
        over_pct = kpis.get("overforecast_rate_percent", 0.0)

        bias_direction = "overforecast" if bias > 0 else "underforecast"
        bias_desc = (
            f"systematic positive bias (+{bias} MW, long position tendency)"
            if bias > 0 else
            f"systematic negative bias ({bias} MW, short position tendency)"
        )

        return (
            f"For delivery on {delivery_date_str}, the Day-Ahead forecast exhibited a Mean Absolute Error of {mae} MW "
            f"({wape}% WAPE) with a {bias_desc}. "
            f"Over {over_pct}% of delivery intervals were overforecasted, indicating that conservative procurement "
            f"should apply an empirical haircut to protect against spot imbalance settlement exposure."
        )
