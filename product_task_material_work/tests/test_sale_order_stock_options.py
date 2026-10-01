# Copyright 2026 Seges
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.product_task_material_work import post_init_hook


@tagged("post_install", "-at_install")
class TestSaleOrderStockOptions(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_type = cls.env.ref(
            "product_task_material_work.stock_picking_type_task_material"
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})
        cls.empty_vals = {
            "picking_type_id": False,
            "location_id": False,
            "location_dest_id": False,
        }

    def _assert_default_stock_options(self, order):
        self.assertEqual(order.picking_type_id, self.picking_type)
        self.assertEqual(
            order.location_id, self.picking_type.default_location_src_id
        )
        self.assertEqual(
            order.location_dest_id, self.picking_type.default_location_dest_id
        )

    def test_compute_stock_options(self):
        self._assert_default_stock_options(self.order)

    def test_post_init_hook_fills_empty_orders(self):
        self.order.write(self.empty_vals)
        other_type = self.picking_type.copy({"sequence_code": "TM2"})
        kept_order = self.env["sale.order"].create({"partner_id": self.partner.id})
        kept_order.write(dict(self.empty_vals, picking_type_id=other_type.id))
        post_init_hook(self.env)
        self._assert_default_stock_options(self.order)
        # Orders with any stock option already set are not touched
        self.assertEqual(kept_order.picking_type_id, other_type)
        self.assertFalse(kept_order.location_id)
