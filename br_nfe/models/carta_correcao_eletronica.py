# © 2016 Alessandro Fernandes Martini <alessandrofmartini@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CartaCorrecaoEletronicaEvento(models.Model):
    _name = 'carta.correcao.eletronica.evento'

    electronic_doc_id = fields.Many2one(
        'invoice.electronic', string="Documento Eletrônico")

    # Fields CCe
    id_cce = fields.Char(string="ID", size=60)
    datahora_evento = fields.Datetime(string="Data do Evento")
    tipo_evento = fields.Char(string="Código do Evento")
    sequencial_evento = fields.Integer(string="Sequencial do Evento")
    correcao = fields.Text(string="Correção", max_length=1000)
    message = fields.Char(string="Mensagem", size=300)
    protocolo = fields.Char(string="Protocolo", size=30)
