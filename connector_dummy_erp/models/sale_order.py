from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    dummy_erp_integration_id = fields.Many2one("dummy.erp.integration", ondelete="restrict")
    dummy_erp_id = fields.Integer("ID In Dummy ERP")
