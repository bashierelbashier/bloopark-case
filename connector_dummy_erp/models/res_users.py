from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = "res.users"

    dummy_erp_integration_id = fields.Many2one("dummy.erp.integration", ondelete="restrict")
    dummy_erp_id = fields.Integer("ID In Dummy ERP")
