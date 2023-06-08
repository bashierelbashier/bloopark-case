from odoo.tests import tagged, TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestIRCron(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cron_name = 'Cron Test Name'
        cls.integration_name = 'Integration Test Name'
        cls.integratin = cls.env['dummy.erp.integration'].create({
            'name': cls.integration_name,
        })
        cls.cron = cls.env['ir.cron'].create({
            'name': cls.cron_name,
            'model_id': cls.env['ir.model']._get_id('dummy.erp.integration'),
            'dummy_erp_integration_id': cls.integratin.id,
        })

    def test_deleting_cron_job(self):
        ''' Ensure you can't delete a cron job if it is linked to a dummy integration object '''

        with self.assertRaises(UserError), self.cr.savepoint():
            self.cron.unlink()
