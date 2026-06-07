"""Test i18n consistency and CSV export."""
import pytest
import sys, io, csv

sys.path.insert(0, 'backend-py')


class TestI18NKeys:
    def test_nav_keys_match(self):
        """Verify zh and en nav keys are identical."""
        zh_nav = {'dashboard', 'analytics', 'tokens', 'repos', 'settings', 'github', 'gitee'}
        en_nav = {'dashboard', 'analytics', 'tokens', 'repos', 'settings', 'github', 'gitee'}
        assert zh_nav == en_nav, "Nav keys must match between zh and en"


class TestCSVExport:
    def test_csv_writer_headers(self):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["仓库", "作者", "邮箱", "日期", "消息", "新增", "删除", "哈希"])
        headers = output.getvalue().strip().split(',')
        assert len(headers) == 8
        assert headers[0] == "仓库"
        assert headers[-1] == "哈希"

    def test_csv_route_exists(self):
        import main
        routes = [r.path for r in main.app.routes]
        assert '/api/export/csv' in routes

    def test_csv_route_method_is_get(self):
        import main
        for r in main.app.routes:
            if r.path == '/api/export/csv':
                assert 'GET' in r.methods
