from odoo import http
from odoo.http import request
import base64

class SurveyCertificateController(http.Controller):

    @http.route('/survey/certificate/preview/<int:survey_id>', type='http', auth='user', website=True)
    def certificate_preview(self, survey_id, **kwargs):
        """Preview certificate in browser without download"""
        
        survey = request.env['survey.survey'].browse(survey_id)
        
        if not survey.exists() or not survey.certification:
            return request.not_found()
        
        # Create fake user input for preview
        fake_user_input = request.env['survey.user_input'].sudo().create({
            'survey_id': survey.id,
            'email': request.env.user.email or 'demo@example.com',
            'partner_id': request.env.user.partner_id.id,
            'test_entry': True,
        })
        
        # Generate certificate image
        if survey.certificate_template_id:
            cert_image = fake_user_input.certification_report_image
            
            if cert_image:
                # Return image directly to browser
                return request.make_response(
                    base64.b64decode(cert_image),
                    headers=[
                        ('Content-Type', 'image/png'),
                        ('Content-Disposition', 'inline; filename="certificate_preview.png"')
                    ]
                )
        
        # Fallback: generate PDF preview
        report = request.env.ref('survey.certification_report')
        pdf_content, _ = report.sudo()._render_qweb_pdf([fake_user_input.id])
        
        # Clean up fake entry
        fake_user_input.sudo().unlink()
        
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'inline; filename="certificate_preview.pdf"')
            ]
        )
