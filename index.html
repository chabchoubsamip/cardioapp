<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Fiche Pré-Consultation Cardiologique</title>

<style>
body { font-family: Arial; margin:40px; background:#f4f6f9;}
.container {background:white; padding:30px; max-width:900px; margin:auto; border-radius:8px;}
.section {margin-bottom:30px;}
h2 {border-bottom:2px solid #0077cc;}
button {padding:12px; background:#0077cc; color:white; border:none; margin-top:20px;}
</style>
</head>

<body>

<div class="container">
<h1>Fiche Pré-Consultation Cardiologique</h1>

<form id="form">

<div class="section">
<h2>Administratif</h2>
Nom <input name="nom" required><br><br>
Prénom <input name="prenom" required><br><br>
Date naissance <input type="date" name="naissance" required><br>
</div>

<div class="section">
<h2>Motif</h2>
<label><input type="radio" name="motif" value="consultation" required> Consultation</label>
</div>

<div class="section">
<h2>Facteurs de risque</h2>
Tabac <select name="tabac"><option>oui</option><option>non</option></select><br>
HTA <select name="hta"><option>oui</option><option>non</option></select>
</div>

<div class="section">
<h2>Antécédents cardiovasculaires</h2>
<label><input type="checkbox" name="ac_arhythmie"> Arythmie</label><br>
<label><input type="checkbox" name="ac_infarctus"> Infarctus</label><br>
Commentaire <input name="ac_commentaire">
</div>

<button type="submit">Envoyer la fiche</button>

</form>
</div>

<script>
document.getElementById("form").addEventListener("submit", async function(e){

    e.preventDefault();
    const f = e.target;

    const motif = document.querySelector('input[name="motif"]:checked');

    const data = {
        administratif:{
            nom:f.nom.value,
            prenom:f.prenom.value,
            naissance:f.naissance.value
        },
        motif_consultation:{
            motif:motif ? motif.value : ""
        },
        facteurs_risque:{
            tabac:f.tabac.value,
            hta:f.hta.value
        },
        antecedents_cardio:{
            arythmie:f.ac_arhythmie.checked,
            infarctus:f.ac_infarctus.checked,
            commentaire:f.ac_commentaire.value
        },
        traitement_ocr:"",
        consentement:{ok:true}
    };

    const res = await fetch("/submit",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(data)
    });

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    window.location.href = url;
});
</script>

</body>
</html>