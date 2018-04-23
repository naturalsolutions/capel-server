#!/usr/bin/env python3
import io
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


class Applicant(object):
    def __init__(self, properties):
        self.properties = properties


class Boat(object):
    def __init__(self, name, matriculation):
        self.name = name
        self.matriculation = matriculation


class Permit(object):
    def __init__(
            self,
            applicant,
            boat=None,
            site=['Parc national de Port-Cros'],
            author='CAPEL',
            title='Autorisation de ...',
            subject='Plonger au coeur du parc',
            template='assets/reglement_2017.pdf',
            save_path='/dev/null'):
        self.applicant = applicant
        self.boat = boat
        self.site = site
        self.author = author
        self.title = title
        self.subject = subject
        self.template = template
        self.save_path = save_path

    def save(self):
        outputStream = io.BytesIO()
        c = canvas.Canvas(outputStream, pagesize=A4)
        c.setAuthor(self.author)
        c.setTitle(self.title)
        c.setSubject(self.subject)

        font_size = 12
        c.setStrokeColorRGB(0, 0, 0)
        c.setFillColorRGB(0, 0, 0)
        c.setFont('Helvetica', font_size)
        textobject = c.beginText()

        for prop in self.applicant.properties:
            value, x, y = prop
            textobject.setTextOrigin(x, y)
            textobject.textLine(value)

        if self.boat not in (None, 'null'):
            value, x, y = self.boat
            if isinstance(value, list):
                value = ', '.join([boat for boat in value])

            textobject.setTextOrigin(x, y)
            textobject.textLine(value)

        c.drawText(textobject)
        c.save()

        template = PdfFileReader(self.template, 'rb')
        n = template.getNumPages()

        user_data = PdfFileReader(outputStream)
        outputStream.seek(0)

        merged = PdfFileWriter()

        for i in range(0, n - 2):
            print('getNumPages:', i)
            page = template.getPage(i)
            merged.addPage(page)

        page = template.getPage(n - 1)
        page.mergePage(user_data.getPage(0))
        merged.addPage(page)

        with open(self.save_path, 'wb') as pdf_output:  # noqa
            merged.write(pdf_output)
