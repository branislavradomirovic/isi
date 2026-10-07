from pathlib import Path

from src.streamlit_app.xai_charts import Chart, render_chart


class UI:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        return lambda *args, **kwargs: self.calls.append((name, args, kwargs))


def test_unavailable_never_emits_svg():
    ui = UI()
    render_chart(ui, Chart(unavailable='NOT_ESTIMATED'))
    assert [call[0] for call in ui.calls] == ['info']


def test_existing_ui_consumes_scoped_result_and_preserves_tables():
    simpa = Path('src/streamlit_app/simpa_analytics_workspace.py').read_text()
    ordo = Path('src/streamlit_app/ordo_analytics_workspace.py').read_text()
    assert 'render_chart(st, coefficient_chart(item))' in simpa
    assert 'st.dataframe(xai["coefficients"]' in simpa
    assert 'render_chart(st, forecast_chart(detail))' in ordo
    assert 'backtest_chart(detail, position)' in ordo
    assert 'key=f"ordo_xai_origin_{selected_id}"' in ordo
    assert 'st.dataframe(points' in ordo and 'st.json(xai["backtest_records"])' in ordo
    for source in (simpa, ordo):
        assert 'def _scope' in source and 'workspace' in source


def test_real_streamlit_render_and_keyboard_equivalent_origin_selection():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_string('''
import streamlit as st
from src.streamlit_app.xai_charts import backtest_chart, render_chart
result = {'schema_version':'ORDO-FORECAST-RUN-v1','result_status':'ESTIMATED',
 'backtest_records':[{'test_start':2,'actual':[1,3],'forecast':[2,2]},
                     {'test_start':3,'actual':[3,4],'forecast':[3,3]}]}
position = st.selectbox('Backtest poreklo / origin',[0,1])
chart = backtest_chart(result,position)
render_chart(st,chart)
st.dataframe(list(chart.rows))
''').run()
    assert not app.exception
    assert 'Index 2' in app.markdown[0].value
    app.selectbox[0].select(1).run()
    assert not app.exception
    assert 'Index 4' in app.markdown[0].value and 'Index 2' not in app.markdown[0].value
    assert app.dataframe[0].value['actual'].tolist() == [3, 4]
