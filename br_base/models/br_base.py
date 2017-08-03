# -*- coding: utf-8 -*-
# © 2009  Renato Lima - Akretion
# © 2015  Michell Stuttgart - KMEE
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class ResStateCity(models.Model):
    """ Este objeto persiste todos os municípios relacionado a um estado.
    No Brasil é necessário em alguns documentos fiscais informar o código
    do IBGE dos município envolvidos da transação.
    """
    _name = 'res.state.city'
    _description = u'Município'

    name = fields.Char(string='Nome', size=64, required=True)
    state_id = fields.Many2one(comodel_name='res.country.state',
                               string='Estado',
                               required=True)
    ibge_code = fields.Char(string=u'Código IBGE', size=7, copy=False)
