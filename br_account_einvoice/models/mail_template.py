# -*- coding: utf-8 -*-

from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    # Campo utilizando apenas para ser utilizado em domains
    model = fields.Char(store=True)

