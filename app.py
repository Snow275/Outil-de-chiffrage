from flask import Flask, render_template, request, session, send_file, jsonify
import pandas as pd
from io import BytesIO
import json

# Fonction pour chercher le prix unitaire et l'unité
def find_prix_unitaire(description):
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Parcourir les sous-détails pour trouver la description
    for lot in data['lots']:
        for sous_detail in lot['sous_details']:
            if sous_detail['description'].strip().lower() == description.strip().lower():
                return sous_detail['prix_unitaire'], sous_detail['unite']

    return 0, "U"  # Si non trouvé

@app.route('/get-prix-unitaire', methods=['POST'])
def get_prix_unitaire():
    data = request.json
    description = data.get('description')

    prix_unitaire, unite = find_prix_unitaire(description)
    if prix_unitaire == 0:
        return jsonify({'error': 'Sous-détail introuvable'}), 404

    return jsonify({
        'prix_unitaire': prix_unitaire,
        'unite': unite
    })


app = Flask(__name__)
app.secret_key = 'dynamic_lots_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data-entry', methods=['GET', 'POST'])
def data_entry():
    if request.method == 'POST':
        # Récupération des sous-détails uniquement
        descriptions = request.form.getlist('sub_description[]')
        quantities = request.form.getlist('sub_quantity[]')
        units = request.form.getlist('sub_unit[]')

        all_sub_details = []
        total_global = 0

        for i in range(len(descriptions)):
            description = descriptions[i]
            quantity = float(quantities[i]) if quantities[i] else 0

            # 🔄 Récupérer le prix unitaire depuis la description
            prix_unitaire, unite = find_prix_unitaire(description)

            total = prix_unitaire * quantity
            total_global += total

            all_sub_details.append({
                'description': description,
                'quantity': quantity,
                'unit': unite,
                'unit_price': prix_unitaire,
                'total': total
            })

        # Stocker dans la session
        session['all_lots'] = all_lots
        session['all_sub_details'] = all_sub_details
        session['total_global'] = total_global

        return render_template('results.html', lots=all_lots, sub_details=all_sub_details, total_global=total_global)

    return render_template('data_entry.html')

@app.route('/export')
def export():
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    # Récupération des données depuis la session
    all_lots = session.get('all_lots', [])
    all_sub_details = session.get('all_sub_details', [])
    total_global = session.get('total_global', 0)

    # Création du fichier Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "DPGF"

    # Définition des styles
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill("solid", fgColor="007BFF")
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal="center", vertical="center")
    bold_font = Font(bold=True, size=12)

    # Titre principal
    ws.merge_cells("A1:F1")
    ws["A1"] = "Décomposition du Prix Global et Forfaitaire (DPGF)"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = center_align

    # En-têtes
    headers = ["Lot", "Description", "Quantité", "Unité", "Prix Unitaire (€)", "Total (€)"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Insertion des données
    current_row = 4

    # Lots principaux
    for lot in all_lots:
        ws.cell(row=current_row, column=1, value=lot['lot_name'])
        ws.cell(row=current_row, column=2, value=lot['description'])
        ws.cell(row=current_row, column=3, value=lot['quantity'])
        ws.cell(row=current_row, column=4, value=lot['unit'])
        ws.cell(row=current_row, column=5, value=lot['unit_price'])
        ws.cell(row=current_row, column=6, value=lot['total'])

        # Appliquer les styles pour chaque cellule
        for col in range(1, 7):
            cell = ws.cell(row=current_row, column=col)
            cell.border = thin_border
            cell.alignment = center_align

        current_row += 1

    # Sous-détails
    for sub in all_sub_details:
        ws.cell(row=current_row, column=1, value="Sous-Détail")
        ws.cell(row=current_row, column=2, value=sub['description'])
        ws.cell(row=current_row, column=3, value=sub['quantity'])
        ws.cell(row=current_row, column=4, value=sub['unit'])
        ws.cell(row=current_row, column=5, value=sub['unit_price'])
        ws.cell(row=current_row, column=6, value=sub['total'])

        # Appliquer les styles pour chaque cellule
        for col in range(1, 7):
            cell = ws.cell(row=current_row, column=col)
            cell.border = thin_border
            cell.alignment = center_align

        current_row += 1

    # Total global
    ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=5)
    ws.cell(row=current_row, column=1, value="TOTAL GLOBAL").font = bold_font
    ws.cell(row=current_row, column=6, value=total_global).font = bold_font

    for col in range(1, 7):
        cell = ws.cell(row=current_row, column=col)
        cell.border = thin_border
        cell.alignment = center_align

    # Ajustement des largeurs de colonnes
    column_widths = [20, 40, 15, 15, 20, 20]
    for i, width in enumerate(column_widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = width

    # Sauvegarde dans un fichier en mémoire
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="DPGF_Resultats_Dynamiques.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == '__main__':
    app.run(debug=True)
