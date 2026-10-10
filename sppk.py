"""Mesin perhitungan SPPK: AHP (bobot kriteria) dan TOPSIS (ranking kecocokan posisi) + prioritas latihan berbobot."""
import math

POSITIONS = ["Goalkeeper", "Fixo/Anchor", "Ala/Flank", "Pivot"]

# Random Index Saaty (n = 1..15)
RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41,
      9: 1.45, 10: 1.49, 11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59}


SKILL_MAX = 10           # skala skill 1-10
TOP_RECOMMENDATIONS = 5  # jumlah kriteria yang direkomendasikan latihan

SAATY = [9, 8, 7, 6, 5, 4, 3, 2, 1, 1 / 2, 1 / 3, 1 / 4, 1 / 5, 1 / 6, 1 / 7, 1 / 8, 1 / 9]
SAATY_LABEL = {1: "sama penting", 3: "sedikit lebih penting", 5: "lebih penting", 7: "sangat lebih penting", 9: "mutlak lebih penting"}


class Profiles(dict):
    """Matriks kepentingan tersimpan per posisi {pos: matriks} + sumbernya {pos: 'pakar' | 'contoh' | 'kosong'}."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.sources = {}

    @property
    def matrices(self):
        return self



def ahp_pos(profiles, p):
    """AHP untuk posisi p memakai matriks kepentingan tersimpan (diisi pakar sekali di awal)."""
    return ahp(profiles[p])


def parse_saaty(text):
    """'3' -> 3.0, '1/3' -> 0.333; dibatasi ke skala Saaty 1/9..9."""
    text = str(text).strip()
    v = 1 / float(text.split("/")[1]) if "/" in text else float(text)
    return min(9.0, max(1 / 9, v))


def ahp(matrix):
    """Hitung bobot (rata-rata baris matriks ternormalisasi), lambda max, CI, CR dari matriks kepentingan pakar."""
    n = len(matrix)
    manual = True
    m = matrix
    col_sum = [sum(m[i][j] for i in range(n)) for j in range(n)]
    norm = [[m[i][j] / col_sum[j] for j in range(n)] for i in range(n)]
    w = [sum(r) / n for r in norm]
    aw = [sum(m[i][j] * w[j] for j in range(n)) for i in range(n)]
    ratio = [aw[i] / w[i] for i in range(n)]
    lam = sum(ratio) / n
    ci = (lam - n) / (n - 1) if n > 1 else 0
    ri = RI.get(n, 1.59)
    cr = ci / ri if ri else 0
    return {"manual": manual, "matrix": m, "col_sum": col_sum, "normalized": norm, "weights": w, "aw": aw, "ratio": ratio, "n": n,
            "lambda_max": lam, "ci": ci, "ri": ri, "cr": cr, "consistent": cr < 0.1}


def inconsistency_hints(names, matrix, weights, top=5):
    """Petunjuk perbaikan matriks tidak konsisten.

    Untuk setiap pasangan (i<j), bobot hasil penilaian lain menyiratkan aᵢⱼ ≈ wᵢ/wⱼ. Pasangan dengan
    selisih log terbesar antara nilai pakar dan nilai tersirat adalah yang paling bertentangan; sarannya
    = nilai skala Saaty terdekat dengan wᵢ/wⱼ (hanya petunjuk, pakar tetap yang memutuskan).
    """
    out = []
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            implied = weights[i] / weights[j]
            err = abs(math.log(matrix[i][j]) - math.log(implied))
            sug = min(SAATY, key=lambda s: abs(math.log(s) - math.log(implied)))
            out.append({"i": i, "j": j, "a": names[i], "b": names[j], "current": matrix[i][j],
                        "implied": implied, "suggest": sug, "err": err})
    out.sort(key=lambda h: h["err"], reverse=True)
    return [h for h in out[:top] if abs(h["suggest"] - h["current"]) > 1e-9]


def topsis(matrix, weights):
    """TOPSIS, semua kriteria benefit. matrix: list baris alternatif x kriteria."""
    if not matrix:
        return []
    k = len(weights)
    den = [math.sqrt(sum(r[j] ** 2 for r in matrix)) or 1 for j in range(k)]
    v = [[weights[j] * r[j] / den[j] for j in range(k)] for r in matrix]
    a_pos = [max(r[j] for r in v) for j in range(k)]
    a_neg = [min(r[j] for r in v) for j in range(k)]
    out = []
    for r in v:
        dp = math.sqrt(sum((r[j] - a_pos[j]) ** 2 for j in range(k)))
        dm = math.sqrt(sum((r[j] - a_neg[j]) ** 2 for j in range(k)))
        out.append({"d_plus": dp, "d_minus": dm, "ci": dm / (dp + dm) if dp + dm else 0})
    return out


def topsis_steps(matrix, weights):
    """Semua langkah TOPSIS untuk ditampilkan/di-export: X, pembagi, R, V, A+, A-, D+, D-, Ci, urutan rank."""
    k = len(weights)
    den = [math.sqrt(sum(r[j] ** 2 for r in matrix)) or 1 for j in range(k)]
    norm = [[r[j] / den[j] for j in range(k)] for r in matrix]
    v = [[weights[j] * r[j] for j in range(k)] for r in norm]
    a_pos = [max(r[j] for r in v) for j in range(k)]
    a_neg = [min(r[j] for r in v) for j in range(k)]
    res = topsis(matrix, weights)
    order = sorted(range(len(matrix)), key=lambda i: res[i]["ci"], reverse=True)
    rank = {i: r + 1 for r, i in enumerate(order)}
    return {"x": matrix, "den": den, "norm": norm, "v": v, "a_pos": a_pos, "a_neg": a_neg,
            "res": res, "order": order, "rank": rank, "w": weights}


def _n(v, d=4):
    return f"{v:.{d}f}"


def _frac(v):
    if v >= 1:
        return str(int(round(v))) if abs(v - round(v)) < 1e-6 else f"{v:.3f}"
    return f"1/{int(round(1 / v))}" if abs(1 / v - round(1 / v)) < 1e-6 else f"{v:.3f}"


def ahp_example(names, a, i=0, j=1):
    """Contoh perhitungan AHP langkah demi langkah dengan angka nyata. Return list (judul, rumus, substitusi)."""
    n, m, w = a["n"], a["matrix"], a["weights"]
    ci_, cj = names[i], names[j]
    aij = m[i][j]
    col = [m[k][i] for k in range(n)]
    row = a["normalized"][i]
    lbl = SAATY_LABEL.get(round(aij)) if aij >= 1 else None
    step1 = ("1. Elemen matriks perbandingan (penilaian pakar, ditetapkan sekali)",
             "aᵢⱼ = penilaian pakar pada skala Saaty 1–9 ;  aⱼᵢ = 1/aᵢⱼ ;  aᵢᵢ = 1",
             f"Pakar menilai {ci_} vs {cj} = {_frac(aij)}{' (' + lbl + ')' if lbl else ''};  maka a({cj},{ci_}) = {_frac(m[j][i])}")
    return [
        step1,
        ("2. Jumlah kolom",
         "Σⱼ = Σᵢ aᵢⱼ",
         f"Kolom {ci_}: " + " + ".join(_frac(x) for x in col) + f" = {_n(a['col_sum'][i], 3)}"),
        ("3. Normalisasi",
         "rᵢⱼ = aᵢⱼ / Σⱼ",
         f"r({ci_},{ci_}) = {_frac(m[i][i])} / {_n(a['col_sum'][i], 3)} = {_n(row[i])}"),
        ("4. Bobot prioritas (rata-rata baris)",
         "wᵢ = (Σⱼ rᵢⱼ) / n",
         f"w({ci_}) = (" + " + ".join(_n(x, 3) for x in row) + f") / {n} = {_n(sum(row))} / {n} = {_n(w[i])}"),
        ("5. Vektor jumlah tertimbang",
         "(Aw)ᵢ = Σⱼ aᵢⱼ · wⱼ",
         f"(Aw)({ci_}) = " + " + ".join(f"{_frac(m[i][k])}×{_n(w[k])}" for k in range(n)) + f" = {_n(a['aw'][i])};  "
         f"(Aw)/w = {_n(a['aw'][i])} / {_n(w[i])} = {_n(a['ratio'][i])}"),
        ("6. Lambda maksimum",
         "λmax = (Σᵢ (Aw)ᵢ / wᵢ) / n",
         "λmax = (" + " + ".join(_n(x, 3) for x in a["ratio"]) + f") / {n} = {_n(a['lambda_max'])}"),
        ("7. Indeks konsistensi",
         "CI = (λmax − n) / (n − 1)",
         f"CI = ({_n(a['lambda_max'])} − {n}) / ({n} − 1) = {_n(a['ci'])}"),
        ("8. Rasio konsistensi",
         "CR = CI / RI ;  konsisten jika CR < 0,1",
         f"CR = {_n(a['ci'])} / {a['ri']} = {_n(a['cr'])} → {'KONSISTEN' if a['consistent'] else 'TIDAK KONSISTEN'}"),
    ]


def topsis_example(names, codes, st, p=0, j=0):
    """Contoh perhitungan TOPSIS untuk pemain indeks p pada kriteria j. Return list (judul, rumus, substitusi)."""
    x, k = st["x"], len(st["w"])
    fx = lambda v: str(v) if isinstance(v, int) else _n(v)
    col = [r[j] for r in x]
    vcol = [r[j] for r in st["v"]]
    r = st["res"][p]
    cn, pc = names[j], codes[p]
    return [
        ("1. Pembagi normalisasi",
         "√Σᵢ xᵢⱼ²",
         f"Kolom {cn}: √(" + " + ".join(f"{fx(v)}²" for v in col) + f") = √{fx(sum(v * v for v in col))} = {_n(st['den'][j])}"),
        ("2. Normalisasi",
         "rᵢⱼ = xᵢⱼ / √Σᵢ xᵢⱼ²",
         f"r({pc},{cn}) = {fx(x[p][j])} / {_n(st['den'][j])} = {_n(st['norm'][p][j])}"),
        ("3. Normalisasi terbobot",
         "vᵢⱼ = wⱼ · rᵢⱼ",
         f"v({pc},{cn}) = {_n(st['w'][j])} × {_n(st['norm'][p][j])} = {_n(st['v'][p][j])}"),
        ("4. Solusi ideal positif & negatif (kriteria benefit)",
         "A⁺ⱼ = max(vᵢⱼ) ;  A⁻ⱼ = min(vᵢⱼ)",
         f"Kolom {cn}: A⁺ = max({', '.join(_n(v) for v in vcol)}) = {_n(st['a_pos'][j])};  A⁻ = {_n(st['a_neg'][j])}"),
        ("5. Jarak ke solusi ideal positif",
         "D⁺ᵢ = √Σⱼ (vᵢⱼ − A⁺ⱼ)²",
         f"D⁺({pc}) = √(" + " + ".join(f"({_n(st['v'][p][c])} − {_n(st['a_pos'][c])})²" for c in range(k)) +
         f") = {_n(r['d_plus'])}"),
        ("6. Jarak ke solusi ideal negatif",
         "D⁻ᵢ = √Σⱼ (vᵢⱼ − A⁻ⱼ)²",
         f"D⁻({pc}) = √(" + " + ".join(f"({_n(st['v'][p][c])} − {_n(st['a_neg'][c])})²" for c in range(k)) +
         f") = {_n(r['d_minus'])}"),
        ("7. Nilai preferensi",
         "Cᵢ = D⁻ᵢ / (D⁺ᵢ + D⁻ᵢ) ;  0 ≤ Cᵢ ≤ 1, makin besar makin cocok",
         f"C({pc}) = {_n(r['d_minus'])} / ({_n(r['d_plus'])} + {_n(r['d_minus'])}) = {_n(r['ci'])} → ranking {st['rank'][p]} dari {len(x)}"),
    ]


def position_topsis(profiles, skills):
    """TOPSIS per pemain dengan alternatif = posisi (penentu posisi terbaik).

    Matriks keputusan X (posisi × kriteria): x_pj = bobot AHP kriteria j untuk posisi p
      -> seberapa besar posisi p menuntut kriteria j (hasil AHP dipakai langsung).
    Vektor bobot TOPSIS: w_j = s_j / Σs, profil skill pemain yang dinormalisasi
      -> kriteria yang menjadi kekuatan pemain mendapat pengaruh lebih besar.
    Semua kriteria benefit. Posisi dengan Cᵢ tertinggi = posisi yang paling banyak menuntut
    kekuatan pemain tersebut.
    """
    n_pos, k = len(POSITIONS), len(skills)
    wpos = [ahp_pos(profiles, p)["weights"] for p in range(n_pos)]
    total = sum(skills) or 1
    st = topsis_steps([row[:] for row in wpos], [s / total for s in skills])
    st.update({"skills": skills, "skill_total": total})
    return st


def weighted_scores(profiles, skills):
    """Skor pendukung per posisi = Σ (bobot AHP posisi × nilai skill 1-10); skala hasil 1-10."""
    return [sum(w * s for w, s in zip(ahp_pos(profiles, p)["weights"], skills)) for p in range(len(POSITIONS))]


def position_matrix_example(names, st, p=0, j=0):
    """Langkah 0: matriks keputusan dan vektor bobot untuk contoh perhitungan TOPSIS per pemain."""
    pos, cn = POSITIONS[p], names[j]
    sk = st["skills"]
    return [("0a. Matriks keputusan (alternatif = posisi)",
             "xₚⱼ = bobot AHP kriteria j pada posisi p",
             f"x({pos},{cn}) = {_n(st['x'][p][j])}  (dari hasil AHP posisi {pos})"),
            ("0b. Bobot kriteria dari profil skill pemain",
             "wⱼ = sⱼ / Σₖ sₖ",
             f"w({cn}) = {sk[j]} / (" + " + ".join(str(v) for v in sk) + f") = {sk[j]} / {st['skill_total']} = {_n(st['w'][j])}")]


def analyze(criteria, profiles, players, player_id, target_pos):
    """Analisis lengkap satu pemain.

    criteria : list dict {id, name, training}
    profiles : {pos_index: [skor per kriteria]}
    players  : list dict {id, code, skills: [nilai per kriteria]} (pemain aktif)
    """
    ahps = {p: ahp_pos(profiles, p) for p in range(len(POSITIONS))}
    idx = next(i for i, pl in enumerate(players) if pl["id"] == player_id)
    pt = position_topsis(profiles, players[idx]["skills"])
    scores = weighted_scores(profiles, players[idx]["skills"])
    ranking = [{"pos": p, "name": POSITIONS[p], "score": scores[p], **pt["res"][p]} for p in range(len(POSITIONS))]
    ranking.sort(key=lambda x: x["ci"], reverse=True)

    # Prioritas latihan tanpa nilai ideal: kekurangan = 10 − skill (jarak ke skor maksimal),
    # prioritas = kekurangan × bobot AHP posisi target -> skill penting yang masih rendah muncul paling atas.
    w = ahps[target_pos]["weights"]
    skills = players[idx]["skills"]
    gaps = []
    for i, c in enumerate(criteria):
        g = SKILL_MAX - skills[i]
        gaps.append({"criterion": c["name"], "training": c["training"], "trainings": c.get("trainings", []), "skill": skills[i],
                     "gap": g, "weight": w[i], "priority": g * w[i]})
    gaps.sort(key=lambda x: x["priority"], reverse=True)
    recs = [g for g in gaps if g["gap"] > 0][:TOP_RECOMMENDATIONS]
    readiness = sum(w[i] * skills[i] for i in range(len(w))) / SKILL_MAX
    wmax = max(w) or 1
    return {"ranking": ranking, "best": ranking[0], "target": target_pos, "target_name": POSITIONS[target_pos],
            "gaps": gaps, "recommendations": recs, "target_readiness": readiness,
            "importance_profile": [round(x / wmax * SKILL_MAX, 2) for x in w]}


def topsis_all(profiles, players):
    """Cᵢ setiap posisi untuk setiap pemain (TOPSIS per pemain, alternatif = posisi)."""
    return {pl["id"]: [r["ci"] for r in position_topsis(profiles, pl["skills"])["res"]] for pl in players}


def player_cohort_ci(profiles, players):
    """Pembanding: TOPSIS per posisi dengan alternatif = pemain aktif (siapa paling cocok di posisi itu)."""
    mat = [pl["skills"] for pl in players]
    res = {pl["id"]: [] for pl in players}
    for p in range(len(POSITIONS)):
        for pl, r in zip(players, topsis(mat, ahp_pos(profiles, p)["weights"])):
            res[pl["id"]].append(r["ci"])
    return res
