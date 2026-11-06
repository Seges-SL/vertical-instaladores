# © 2025 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    custom_report_footer = fields.Html('Pie del report', translate=True, sanitize=True)

    report_header_image = fields.Binary(
        attachment=True,
        help="Image that replaces the whole header of the external report "
             "layouts when 'Replace standard header with image' is enabled. "
             "It is scaled down to fit the header area of the paper format "
             "(top margin minus 3 mm, about 37 mm with the default European "
             "A4 format).",
    )
    report_header_image_replace = fields.Boolean(
        string="Replace standard header with image",
        default=False,
        help="If enabled (and there is a header image), the standard header "
             "of the external report layouts is replaced by the image.",
    )
    custom_report_footer_replace = fields.Boolean(
        string="Replace standard footer",
        default=False,
        help="If enabled, the custom footer replaces the whole standard "
             "footer of the external report layouts. If disabled, the custom "
             "footer is added after the standard report footer.",
    )
    custom_report_footer_keep_page_numbers = fields.Boolean(
        string="Keep page numbers",
        default=True,
        help="When the custom footer replaces the standard footer, keep the "
             "page numbering band (Page x / y, PDF only) below it.",
    )
