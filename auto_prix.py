import json

def charger_donnees():
    # Charger les données depuis le fichier JSON
    with open('data.json', 'r', encoding='utf-8') as fichier:
        return json.load(fichier)

def obtenir_prix(description_recherchee, donnees):
    # Parcourir les lots et sous-détails pour trouver la description
    for lot in donnees['lots']:
        for sous_detail in lot['sous_details']:
            if sous_detail['description'].lower() == description_recherchee.lower():
                return sous_detail['prix_unitaire']
    return None

def main():
    donnees = charger_donnees()
    
    while True:
        description = input("Entrez la description du produit (ou 'exit' pour quitter) : ")
        if description.lower() == 'exit':
            break
        
        prix = obtenir_prix(description, donnees)
        if prix:
            print(f"Le prix unitaire pour '{description}' est de : {prix} €")
        else:
            print("Description non trouvée. Veuillez réessayer.")

if __name__ == "__main__":
    main()
