# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "analytic.mixin"]

    scrap_ids = fields.One2many(
        comodel_name="stock.scrap", inverse_name="task_id", string="Scraps"
    )
    scrap_count = fields.Integer(
        compute="_compute_scrap_move_count", string="Scrap Move"
    )
    move_ids = fields.One2many(
        comodel_name="stock.move",
        inverse_name="raw_material_task_id",
        string="Stock Moves",
        copy=False,
        domain=[("scrapped", "=", False)],
    )
    use_stock_moves = fields.Boolean(related="stage_id.use_stock_moves")
    done_stock_moves = fields.Boolean(related="stage_id.done_stock_moves")
    stock_moves_is_locked = fields.Boolean(default=True)
    allow_moves_action_confirm = fields.Boolean(
        compute="_compute_allow_moves_action_confirm"
    )
    allow_moves_action_assign = fields.Boolean(
        compute="_compute_allow_moves_action_assign"
    )
    stock_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("assigned", "Assigned"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
        compute="_compute_stock_state",
    )
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
        readonly=False,
        index=True,
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Source Location",
        readonly=False,
        index=True,
        check_company=True,
    )
    location_dest_id = fields.Many2one(
        comodel_name="stock.location",
        string="Destination Location",
        readonly=False,
        index=True,
        check_company=True,
    )
    stock_analytic_date = fields.Date(string="Analytic date")
    stock_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Move Analytic Account",
        help="Move created will be assigned to this analytic account",
    )
    stock_analytic_distribution = fields.Json(
        "Analytic Distribution",
        copy=True,
        readonly=False,
    )
    stock_analytic_line_ids = fields.One2many(
        comodel_name="account.analytic.line",
        inverse_name="stock_task_id",
        string="Analytic Lines",
    )
    group_id = fields.Many2one(
        comodel_name="procurement.group",
    )
    company_id = fields.Many2one(default=lambda self: self.env.company)

    def _compute_scrap_move_count(self):
        data = self.env["stock.scrap"].read_group(
            [("task_id", "in", self.ids)], ["task_id"], ["task_id"]
        )
        count_data = {item["task_id"][0]: item["task_id_count"] for item in data}
        for item in self:
            item.scrap_count = count_data.get(item.id, 0)

    @api.depends("move_ids", "move_ids.state")
    def _compute_allow_moves_action_confirm(self):
        for item in self:
            item.allow_moves_action_confirm = any(
                move.state == "draft" for move in item.move_ids
            )

    @api.depends("move_ids", "move_ids.state")
    def _compute_allow_moves_action_assign(self):
        for item in self:
            item.allow_moves_action_assign = any(
                move.state in ("confirmed", "partially_available")
                for move in item.move_ids
            )

    @api.depends("move_ids", "move_ids.state")
    def _compute_stock_state(self):
        for task in self:
            task.stock_state = "pending"
            if task.move_ids:
                states = task.mapped("move_ids.state")
                for state in ("confirmed", "assigned", "done", "cancel"):
                    if state in states:
                        task.stock_state = state
                        break

    @api.onchange("picking_type_id")
    def _onchange_picking_type_id(self):
        self.location_id = self.picking_type_id.default_location_src_id.id
        self.location_dest_id = self.picking_type_id.default_location_dest_id.id

    def _check_tasks_with_pending_moves(self):
        if self.move_ids and "assigned" in self.mapped("move_ids.state"):
            raise UserError(
                _("It is not possible to change this with reserved movements in tasks.")
            )

    def _update_moves_info(self):
        for item in self:
            item._check_tasks_with_pending_moves()
            picking_type = item.picking_type_id or item.project_id.picking_type_id
            location = item.location_id or item.project_id.location_id
            location_dest = item.location_dest_id or item.project_id.location_dest_id
            moves = item.move_ids.filtered(
                lambda x, loc=location, loc_dest=location_dest: (
                    x.state not in ("cancel", "done")
                    and (x.location_id != loc or x.location_dest_id != loc_dest)
                )
            )
            moves.write(
                {
                    "warehouse_id": location.warehouse_id.id,
                    "location_id": location.id,
                    "location_dest_id": location_dest.id,
                    "picking_type_id": picking_type.id,
                }
            )
        self.action_assign()

    def _update_moves_group_id(self):
        for item in self:
            picking_type = item.picking_type_id or item.project_id.picking_type_id
            location = item.location_id or item.project_id.location_id
            location_dest = item.location_dest_id or item.project_id.location_dest_id
            moves = item.move_ids.filtered(
                lambda x, loc=location, loc_dest=location_dest, pick_type=picking_type: (
                    x.state not in ("cancel", "done")
                    and x.location_id == loc
                    and x.location_dest_id == loc_dest
                    and x.picking_type_id == pick_type
                )
            )
            # Moves already in a picking keep the picking's procurement group
            moves.filtered(lambda x: not x.picking_id).write(
                {"group_id": item.group_id.id}
            )
            item.move_ids.filtered(
                lambda x: not x.task_id and x.state not in ("cancel", "done")
            ).write({"task_id": item.id})

    def _update_analytic_distribution_info(self):
        for item in self:
            picking_type = item.picking_type_id or item.project_id.picking_type_id
            location = item.location_id or item.project_id.location_id
            location_dest = item.location_dest_id or item.project_id.location_dest_id
            moves = item.move_ids.filtered(
                lambda x, loc=location, loc_dest=location_dest, pick_type=picking_type: (
                    x.state not in ("cancel", "done")
                    and x.location_id == loc
                    and x.location_dest_id == loc_dest
                    and x.picking_type_id == pick_type
                )
            )
            moves.write(
                {
                    "analytic_distribution": item.stock_analytic_distribution,
                }
            )

    @api.model
    def _prepare_procurement_group_vals(self):
        return {"name": "Task-ID: %s" % self.id}

    def action_confirm(self):
        # 1. Guardamos los pickings que ya existían previamente
        old_pickings = self.mapped("move_ids.picking_id")
        # 2. Ejecutamos la lógica original de confirmación (creará los nuevos pickings)
        self.move_ids._action_confirm()
        self.move_ids.filtered(
            lambda move: move.state not in ("draft", "cancel", "done")
        )._trigger_scheduler()

        # 3. Calculamos la diferencia para obtener los pickings recién generados
        new_pickings = self.mapped("move_ids.picking_id") - old_pickings
        # 4. Iteramos para dejar el mensaje con enlace en el chatter del nuevo albarán
        for task in self:
            task_pickings = new_pickings & task.move_ids.picking_id
            for picking in task_pickings:
                # Construimos el enlace seguro en HTML nativo de Odoo apuntando al id de la tarea
                task_link = task._get_html_link()
                # Formateamos el mensaje soportando multi-idioma (_)
                msg = Markup(_("This transfer was generated from task: %s")) % task_link
                # Posteamos en el hilo (chatter) del albarán generado. sudo(): el
                # usuario de proyecto puede no tener escritura en stock.picking
                picking.sudo().message_post(
                    body=msg,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )

    def action_assign(self):
        self.action_confirm()
        self.mapped("move_ids")._action_assign()

    def button_scrap(self):
        self.ensure_one()
        move_items = self.move_ids.filtered(lambda x: x.state not in ("done", "cancel"))
        return {
            "name": _("Scrap"),
            "view_mode": "form",
            "res_model": "stock.scrap",
            "view_id": self.env.ref("stock.stock_scrap_form_view2").id,
            "type": "ir.actions.act_window",
            "context": {
                "default_task_id": self.id,
                "product_ids": move_items.mapped("product_id").ids,
                "default_company_id": self.company_id.id,
            },
            "target": "new",
        }

    def action_cancel(self):
        """Cancel the stock moves and remove the analytic lines created from
        stock moves when cancelling the task.
        """
        self.mapped("move_ids.move_line_ids").write({"quantity": 0})
        # Use sudo to avoid error for users with no access to analytic
        self.sudo().stock_analytic_line_ids.unlink()
        self.stock_moves_is_locked = True
        return True

    def action_toggle_stock_moves_is_locked(self):
        self.ensure_one()
        self.stock_moves_is_locked = not self.stock_moves_is_locked
        return True

    def action_done(self):
        picking_ids = self.move_ids.picking_id
        for picking in picking_ids:
            picking.with_context(skip_sanity_check=True).button_validate()
        # Use sudo to avoid error for users with no access to analytic
        analytic_line_model = self.env["account.analytic.line"].sudo()
        for move in self.move_ids:
            vals = move._prepare_analytic_line_from_task()
            if vals:
                analytic_line_model.create(vals)

    def action_see_move_scrap(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_stock_scrap")
        action["domain"] = [("task_id", "=", self.id)]
        action["context"] = dict(self._context, default_origin=self.name)
        return action

    def action_view_delivery(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        pickings = self.move_ids.mapped('picking_id')

        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(view_id, view_type) for view_id, view_type in action['views'] if view_type != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        else:
            action['domain'] = [('id', '=', False)]

        # Preparamos los valores para el contexto
        picking_type_id = False
        group_id = False

        if pickings:
            # Si hay albaranes, priorizamos los de salida o tomamos el primero
            picking_out = pickings.filtered(lambda p: p.picking_type_id.code == 'outgoing')
            picking = picking_out[0] if picking_out else pickings[0]

            picking_type_id = picking.picking_type_id.id
            group_id = picking.group_id.id
        else:
            # FALLBACK: Si no hay albaranes, usamos la config de la tarea o proyecto
            # Lógica consistente con el método _update_moves_info del archivo original
            picking_type = self.picking_type_id or self.project_id.picking_type_id
            if picking_type:
                picking_type_id = picking_type.id
            if self.group_id:
                group_id = self.group_id.id

        # Construimos el contexto final
        cleaned_context = {
            k: v
            for k, v in self._context.items()
            if k != 'form_view_ref' and not k.startswith('default_')
        }
        ctx_vals = {
            'default_partner_id': self.partner_id.id,
            'default_origin': self.name,
        }

        if picking_type_id:
            ctx_vals['default_picking_type_id'] = picking_type_id
        if group_id:
            ctx_vals['default_group_id'] = group_id

        action['context'] = dict(cleaned_context, **ctx_vals)
        return action

    def write(self, vals):
        res = super().write(vals)
        if "stage_id" in vals:
            stage = self.env["project.task.type"].browse(vals.get("stage_id"))
            if stage.done_stock_moves:
                # sudo(): the project user must be able to close the task even
                # without stock permissions; these are internal operations.
                tasks = self.sudo()
                for task in tasks.filtered(lambda t: not t.group_id):
                    task.group_id = self.env["procurement.group"].create(
                        task._prepare_procurement_group_vals()
                    )
                tasks._update_moves_group_id()
                tasks_with_distribution = tasks.filtered("stock_analytic_distribution")
                if tasks_with_distribution:
                    tasks_with_distribution._update_analytic_distribution_info()
                tasks.action_assign()

        # Update info
        field_names = ("location_id", "location_dest_id")
        if any(vals.get(field) for field in field_names):
            self._update_moves_info()
        return res

    def unlink(self):
        # Use sudo to avoid error to users with no access to analytic
        # related to hr_timesheet addon
        return super(ProjectTask, self.sudo()).unlink()


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    use_stock_moves = fields.Boolean(
        help="If you mark this check, when a task goes to this state, "
        "it will use stock moves",
    )
    done_stock_moves = fields.Boolean(
        help="If you check this box, when a task is in this state, you will not "
        "be able to add more stock moves but they can be viewed."
    )
