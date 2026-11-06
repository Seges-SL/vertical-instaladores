# Copyright 2025 Seges
# License AGPL-3 (https://www.gnu.org/licenses/agpl-3.0).
import base64
import io

from PIL import Image

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import is_html_empty

LAYOUTS = {
    'standard': 'o_standard_footer',
    'bold': 'o_clean_footer',
    'boxed': 'o_boxed_footer',
    'striped': 'o_background_footer',
}
STD_FOOTER = 'STDFOOTER_MARK'
CUSTOM_FOOTER = 'CUSTOMFOOTER_MARK'
STD_TAGLINE = 'STDTAGLINE_MARK'
PAGE_BAND = 'o_cfbc_page_numbers'
HEADER_ALT = 'alt="Header"'


@tagged("post_install", "-at_install")
class TestReportLayout(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        buf = io.BytesIO()
        Image.new('RGB', (40, 10), 'red').save(buf, format='PNG')
        cls.image = base64.b64encode(buf.getvalue())
        cls.company = cls.env['res.company'].create({
            'name': 'CFBC Company A',
            'report_footer': f'<p>{STD_FOOTER}</p>',
            'report_header': f'<p>{STD_TAGLINE}</p>',
            'custom_report_footer': f'<p>{CUSTOM_FOOTER}</p>',
        })
        cls.company_b = cls.env['res.company'].create({
            'name': 'CFBC Company B',
            'report_footer': f'<p>{STD_FOOTER}</p>',
            'report_header': f'<p>{STD_TAGLINE}</p>',
            'custom_report_footer': f'<p>{CUSTOM_FOOTER}</p>',
        })

    def _render(self, company, layout):
        view = self.env.ref(f'web.external_layout_{layout}')
        company.external_report_layout_id = view
        partner = self.env['res.partner'].create({
            'name': 'CFBC doc partner', 'company_id': company.id})
        html = self.env['ir.qweb']._render('web.external_layout', {
            'o': partner.with_company(company),
            'report_type': 'pdf',
            'is_html_empty': is_html_empty,
            'display_name_in_footer': False,
            'res_company': company,
        })
        return str(html)

    def test_01_defaults_are_standard(self):
        self.assertFalse(self.company.report_header_image_replace)
        self.assertFalse(self.company.custom_report_footer_replace)
        self.assertTrue(self.company.custom_report_footer_keep_page_numbers)
        self.company.report_header_image = self.image
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertNotIn(HEADER_ALT, html, layout)
            self.assertIn(STD_TAGLINE if layout != 'bold' else STD_FOOTER,
                          html, layout)
            self.assertIn(STD_FOOTER, html, layout)
            self.assertIn('class="page"', html, layout)

    def test_02_header_image_replace(self):
        self.company.write({
            'report_header_image': self.image,
            'report_header_image_replace': True,
        })
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertIn(HEADER_ALT, html, layout)
            self.assertIn('data:image/png;base64,', html, layout)
            self.assertIn('max-height', html, layout)
            # The standard header (tagline) is gone. In bold the tagline is
            # also rendered in the footer, so check the header div directly.
            if layout != 'bold':
                self.assertNotIn(STD_TAGLINE, html, layout)
            self.assertNotIn(f'o_company_{self.company.id}_layout header',
                             html, layout)
            self.assertIn(STD_FOOTER, html, layout)

    def test_03_header_image_switch_off(self):
        self.company.write({
            'report_header_image': self.image,
            'report_header_image_replace': False,
        })
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertNotIn(HEADER_ALT, html, layout)
        # Switch on but no image: also standard
        self.company.write({
            'report_header_image': False,
            'report_header_image_replace': True,
        })
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertNotIn(HEADER_ALT, html, layout)

    def test_04_footer_replace(self):
        self.company.custom_report_footer_replace = True
        for layout, footer_class in LAYOUTS.items():
            html = self._render(self.company, layout)
            self.assertIn(CUSTOM_FOOTER, html, layout)
            self.assertNotIn(STD_FOOTER, html, layout)
            self.assertNotIn(footer_class, html, layout)
            self.assertIn(PAGE_BAND, html, layout)
            self.assertIn('class="page"', html, layout)

    def test_05_footer_replace_without_page_numbers(self):
        self.company.write({
            'custom_report_footer_replace': True,
            'custom_report_footer_keep_page_numbers': False,
        })
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertIn(CUSTOM_FOOTER, html, layout)
            self.assertNotIn(STD_FOOTER, html, layout)
            self.assertNotIn(PAGE_BAND, html, layout)

    def test_06_footer_replace_with_empty_custom_footer(self):
        self.company.write({
            'custom_report_footer_replace': True,
            'custom_report_footer': '<p><br></p>',
        })
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertIn(STD_FOOTER, html, layout)
            self.assertNotIn(PAGE_BAND, html, layout)

    def test_07_footer_legacy_append(self):
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertIn(STD_FOOTER, html, layout)
            self.assertIn(CUSTOM_FOOTER, html, layout)
            self.assertLess(html.index(STD_FOOTER),
                            html.index(CUSTOM_FOOTER), layout)
            self.assertNotIn(PAGE_BAND, html, layout)

    def test_08_multicompany(self):
        self.company.write({
            'report_header_image': self.image,
            'report_header_image_replace': True,
            'custom_report_footer_replace': True,
        })
        for layout in LAYOUTS:
            html_a = self._render(self.company, layout)
            html_b = self._render(self.company_b, layout)
            self.assertIn(HEADER_ALT, html_a, layout)
            self.assertNotIn(STD_FOOTER, html_a, layout)
            self.assertNotIn(HEADER_ALT, html_b, layout)
            self.assertIn(STD_FOOTER, html_b, layout)
            self.assertIn(CUSTOM_FOOTER, html_b, layout)

    def test_09_wizard_preview(self):
        self.company.write({
            'report_header_image': self.image,
            'report_header_image_replace': True,
            'custom_report_footer_replace': True,
            'external_report_layout_id': self.env.ref(
                'web.external_layout_standard').id,
        })
        wizard = self.env['base.document.layout'].with_company(
            self.company).create({})
        wizard.report_layout_id = self.env['report.layout'].search([
            ('view_id.key', '=', 'web.external_layout_standard')], limit=1)
        self.assertTrue(wizard.preview)
        self.assertIn(HEADER_ALT, wizard.preview)
        self.assertIn(CUSTOM_FOOTER, wizard.preview)
        self.assertTrue(wizard.report_header_image_replace)
        wizard.custom_report_footer_replace = False
        self.assertFalse(self.company.custom_report_footer_replace)

    def test_10_header_max_height_follows_paperformat(self):
        self.company.write({
            'report_header_image': self.image,
            'report_header_image_replace': True,
            'paperformat_id': self.env.ref('base.paperformat_euro').id,
        })
        self.assertEqual(self.company.paperformat_id.margin_top, 40)
        paperformat = self.env['report.paperformat'].create({
            'name': 'CFBC top 50',
            'format': 'A4',
            'margin_top': 50,
        })
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertRegex(html, r'max-height: 37(\.0)?mm', layout)
        self.company.paperformat_id = paperformat
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertRegex(html, r'max-height: 47(\.0)?mm', layout)
            self.assertNotRegex(html, r'max-height: 37(\.0)?mm', layout)

    def test_11_footer_height_and_page_numbers_padding(self):
        euro = self.env.ref('base.paperformat_euro')
        self.assertEqual(euro.margin_bottom, 32)
        paperformat = self.env['report.paperformat'].create({
            'name': 'CFBC bottom 40',
            'format': 'A4',
            'margin_bottom': 40,
        })
        self.company.write({
            'custom_report_footer_replace': True,
            'paperformat_id': euro.id,
        })
        self.assertTrue(self.company.custom_report_footer_keep_page_numbers)
        content = r'max-height: %s(\.0)?mm; overflow: hidden;">\s*<div[^>]*>'
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertRegex(html, content % 23, layout)
            self.assertIn(PAGE_BAND, html, layout)
            self.assertIn('padding-bottom: 4mm', html, layout)
            self.assertIn('Page:', html, layout)
        # Different paperformat: margin_bottom - 9
        self.company.paperformat_id = paperformat
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertRegex(html, content % 31, layout)
            self.assertNotRegex(html, content % 23, layout)
        # Without page numbers: full margin_bottom and no numbering block
        self.company.write({
            'paperformat_id': euro.id,
            'custom_report_footer_keep_page_numbers': False,
        })
        for layout in LAYOUTS:
            html = self._render(self.company, layout)
            self.assertRegex(html, content % 32, layout)
            self.assertNotRegex(html, content % 23, layout)
            self.assertNotIn(PAGE_BAND, html, layout)
            self.assertNotIn('padding-bottom: 4mm', html, layout)
