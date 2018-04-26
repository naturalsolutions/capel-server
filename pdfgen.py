#!/usr/bin/env python3
import io
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


class Applicant(object):
    def __init__(self, fullname, phone, email):
        self.fullname = fullname
        self.phone = phone
        self.email = email




class Permit(object):
    def __init__(self,
                 applicant,
                 boat,
                 site=['Parc national de Port-Cros'],
                 template='assets/reglement_2017_de_plongee_sous_marine_dans_les_coeurs_marins_du_parc_national.pdf',  # noqa
                 save_path='/dev/null'):
        self.applicant = applicant
        self.boat = boat
        self.site = site
        self.template = template
        self.save_path = save_path

    def save(self, ):
        x = 55 * mm
        y = 43 * mm
        font_size = 12
        leading = font_size + 5

        outputStream = io.BytesIO()
        c = canvas.Canvas(outputStream, pagesize=A4)
        c.setAuthor('CAPEL')
        c.setTitle('Autorisation de ...')
        c.setSubject('Plonger au coeur du parc')
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(0, 0, 0)
        c.setFont('Helvetica', font_size)
        textobject = c.beginText()
        textobject.setLeading(leading)
        textobject.setTextOrigin(x, y)

        for value in ['fullname', 'phone', 'email']:
            textobject.textLine(getattr(self.applicant, value))
            print(textobject.getX(), textobject.getY())

        c.drawText(textobject)
        c.save()

        template = PdfFileReader(open(self.template, 'rb'))

        user_data = PdfFileReader(outputStream)
        outputStream.seek(0)

        merged = PdfFileWriter()
        page = template.getPage(0)
        merged.addPage(page)

        page = template.getPage(1)
        page.mergePage(user_data.getPage(0))
        merged.addPage(page)

        with open(self.save_path, 'wb') as pdf_output:  # noqa
            merged.write(pdf_output)
