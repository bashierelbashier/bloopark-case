from odoo import fields, models, _
from odoo.exceptions import UserError


class IrCron(models.Model):
    _inherit = "ir.cron"

    dummy_erp_integration_id = fields.Many2one(
        "dummy.erp.integration", "Dummy ERP Integration", ondelete="cascade"
    )

    def unlink(self):
        for rec in self:
            if rec.dummy_erp_integration_id:
                raise UserError(
                    _(
                        "You cannot delete a scheduled job linked to "
                        "Dummy ERP integration (" + rec.dummy_erp_integration_id.name + ")"
                    )
                )
        return super(IrCron, self).unlink()
