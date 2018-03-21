# © 2014 KMEE (http://www.kmee.com.br)
# @author Rafael da Silva Lima <rafael.lima@kmee.com.br>
# @author Matheus Felix <matheus.felix@kmee.com.br>
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Employee\'s Dependents'

    @api.one
    @api.constrains('dependent_age')
    def _check_birth(self):
        dep_age = datetime.strptime(
            self.dependent_age, DEFAULT_SERVER_DATE_FORMAT)
        if dep_age.date() > datetime.now().date():
            raise ValidationError('Data de aniversário inválida')
        return True

    employee_id = fields.Many2one('hr.employee', 'Funcionário')
    dependent_name = fields.Char('Nome', size=64, required=True,
                                 translate=True)
    dependent_age = fields.Date('Data de nascimento', required=True)
    dependent_type = fields.Char('Tipo', required=True)
    pension_benefits = fields.Float(
        '% Pensão', help="Percentual a descontar de pensão alimenticia")
    is_dependent = fields.Boolean('É dependente', required=False)
    use_health_plan = fields.Boolean('Plano de saúde?', required=False)
