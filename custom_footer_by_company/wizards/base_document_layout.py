# © 2025 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    custom_report_footer = fields.Html(related='company_id.custom_report_footer', readonly=False,)
    custom_report_footer_replace = fields.Boolean(
        related='company_id.custom_report_footer_replace', readonly=False)
    custom_report_footer_keep_page_numbers = fields.Boolean(
        related='company_id.custom_report_footer_keep_page_numbers', readonly=False)
    report_header_image = fields.Binary(
        related='company_id.report_header_image', readonly=False)
    report_header_image_replace = fields.Boolean(
        related='company_id.report_header_image_replace', readonly=False)

    @api.depends(
        "custom_report_footer",
        "custom_report_footer_replace",
        "custom_report_footer_keep_page_numbers",
        "report_header_image",
        "report_header_image_replace",
    )
    def _compute_preview(self):
        return super()._compute_preview()