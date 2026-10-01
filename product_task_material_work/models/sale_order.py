# © 2024 Liyben
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, exceptions, _

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    
    _inherit='sale.order'

    #Numero de cliente
    ref = fields.Char(related='partner_id.ref', store=True, string='Nº. Cliente', precompute=True)

    #Campos para el stock desde la tarea
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Tipo de operación",
        readonly=False,
        domain="[('company_id', '=', company_id)]",
        index=True,
        check_company=True,
        compute='_compute_stock_options', 
        store=True,
        precompute=True,
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Ubicación de origen",
        readonly=False,
        check_company=True,
        index=True,
        compute='_compute_stock_options', 
        store=True,
        precompute=True,
    )
    location_dest_id = fields.Many2one(
        comodel_name="stock.location",
        string="Ubicación destino",
        readonly=False,
        index=True,
        check_company=True,
        compute='_compute_stock_options', 
        store=True,
        precompute=True,
    )

    @api.depends('company_id')
    def _compute_stock_options(self):
        for order in self:
            default_picking_type_id = self.env['ir.default'].with_company(
                order.company_id.id)._get_model_defaults('sale.order').get('picking_type_id')
            default_location_id = self.env['ir.default'].with_company(
                order.company_id.id)._get_model_defaults('sale.order').get('location_id')
            default_location_dest_id = self.env['ir.default'].with_company(
                order.company_id.id)._get_model_defaults('sale.order').get('location_dest_id')
            
            # Al instalar el módulo (o actualizar desde 14.0) este compute se
            # ejecuta antes de cargar data/stock_picking_type_data.xml; esos
            # pedidos se completan después con _recompute_empty_stock_options().
            picking_type = self.env.ref(
                'product_task_material_work.stock_picking_type_task_material',
                raise_if_not_found=False,
            ) or self.env['stock.picking.type']

            if default_picking_type_id is not None:
                order.picking_type_id = default_picking_type_id
            else:
                order.picking_type_id = picking_type.id

            if default_location_id is not None:
                order.location_id = default_location_id
            else:
                order.location_id = picking_type.default_location_src_id.id

            if default_location_dest_id is not None:
                order.location_dest_id = default_location_dest_id
            else:
                order.location_dest_id = picking_type.default_location_dest_id.id

    @api.model
    def _recompute_empty_stock_options(self):
        """Rellena tipo de operación y ubicaciones de los pedidos que los
        tienen vacíos. Se usa en el post_init_hook y en la migración desde
        14.0, cuando ya existe el tipo de operación del módulo."""
        orders = self.with_context(active_test=False).search([
            ('picking_type_id', '=', False),
            ('location_id', '=', False),
            ('location_dest_id', '=', False),
        ])
        orders._compute_stock_options()
        return orders

    def action_confirm(self):
        res = super().action_confirm()
        if self.env.user.has_group('product_task_material_work.group_sales_merge_task_to_confirm') and len(self.order_line.mapped('auto_create_task')) > 1:
            return {'type': 'ir.actions.act_window',
                'name': _('Combinar partes de trabajo'),
                'res_model': 'sale.order.merge.task.wizard',
                'target': 'new',
                'view_id': self.env.ref('product_task_material_work.view_sale_order_merge_task').id,
                'view_mode': 'form'}
                
        return res

    #Se añade la cuenta anañitica a la distribución analitica de cada linea despues de crearla
    def _create_analytic_account(self, prefix=None):
        result = super(SaleOrder, self)._create_analytic_account(prefix=prefix)
        for order in self:
            analytic_account_id = order.analytic_account_id.id
            if analytic_account_id:
                analytic_account_id = str(analytic_account_id)
                for line in order.order_line:
                    line.analytic_distribution = {analytic_account_id: 100}
        return result
    
    def get_report_pages_flat(self, lines_to_report):
        """
        Devuelve una lista de listas de líneas.
        Ejemplo: [ [LíneaSeccion1, Prod1, Prod2], [LíneaSeccion2(Salto), Prod3] ]
        """
        pages = []
        current_page = []

        for line in lines_to_report:
            # Si es una sección y tiene activado el salto de página...
            if line.display_type == 'line_section' and line.layout_category_id.pagebreak:
                # Si ya tenemos una página acumulada, la guardamos y empezamos una nueva
                if current_page:
                    pages.append(current_page)
                # La nueva página empieza con esta línea de sección
                current_page = [line]
            else:
                # Si no, añadimos la línea a la página actual
                current_page.append(line)

        # Añadimos la última página si tiene contenido
        if current_page:
            pages.append(current_page)

        return pages