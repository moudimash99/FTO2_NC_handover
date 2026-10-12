# -*- coding: utf-8 -*-
"""
Foundry (Skywise) wrapper for the CNQ step.  TEMPLATE - NOT YET RUN IN FOUNDRY.

It sits right after the step that calls the defect parser:

    Skywise NC source --> defect parser step --> FTO2 NC dataset + FTO2 defects dataset
                                                        |
                                                 this CNQ step
                                                        |
                                    fto2_nc_cnq + fto2_defects_cnq --> Slate queries --> bar charts

What to do:
  1. Copy the `cnq` folder into the code repository, next to the parser.
  2. Replace the four <...> dataset paths below.
  3. Make sure the NC dataset carries the columns listed in NC_REQUIRED (see cnq_core.py):
     today's v4.7 output lacks `decision_status` and `liability`, and for full detail `type_nc` and `produit`.
  4. Build. Compare the totals with tests/expected_totals.json.

The data is small (under 1,000 NCs, a few thousand defect lines), so it is converted to pandas,
the same calculation as the local test is run, and the result is written back.
"""
from transforms.api import transform, Input, Output

from .cnq_core import compute_cnq


def _to_spark(ctx, pdf):
    # Spark cannot guess the type of a column that is entirely empty (e.g. `sub_code` in v4.7): drop those.
    pdf = pdf.dropna(axis=1, how="all")
    return ctx.spark_session.createDataFrame(pdf)


@transform(
    out_nc=Output("<PATH>/fto2_nc_cnq"),
    out_defects=Output("<PATH>/fto2_defects_cnq"),
    nc=Input("<PATH>/fto2_nc"),
    defects=Input("<PATH>/fto2_defects"),
)
def compute(ctx, out_nc, out_defects, nc, defects):
    nc_out, defects_out = compute_cnq(nc.dataframe().toPandas(), defects.dataframe().toPandas())
    out_nc.write_dataframe(_to_spark(ctx, nc_out))
    out_defects.write_dataframe(_to_spark(ctx, defects_out))
