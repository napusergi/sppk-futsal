"""Mesin perhitungan SPPK: AHP (bobot kriteria) dan TOPSIS (ranking kecocokan posisi) + analisis gap."""
import math

POSITIONS = ["Goalkeeper", "Fixo/Anchor", "Ala/Flank", "Pivot"]

# Random Index Saaty (n = 1..15)
RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41,
      9: 1.45, 10: 1.49, 11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59}


def category(score):
    """Kategori kualitatif dari skor kebutuhan 1-9."""
    return "High" if score >= 7 else "Medium" if score >= 4 else "Low"


def pairwise_matrix(scores):
    """Matriks perbandingan berpasangan otomatis dari skor kebutuhan (1-9).

    Selisih d = s_i - s_j  ->  a_ij = d + 1 (d >= 0)  atau  1 / (1 - d) (d < 0), dibatasi skala Saaty 1-9.
    """
    m = []
    for a in scores:
        row = []
        for b in scores:
            d = a - b
            row.append(min(9, d + 1) if d >= 0 else 1 / min(9, 1 - d))
        m.append(row)
    return m


def ahp(scores):
    """Hitung bobot (rata-rata baris matriks ternormalisasi), lambda max, CI, CR."""
    n = len(scores)
    m = pairwise_matrix(scores)
    col_sum = [sum(m[i][j] for i in range(n)) for j in range(n)]
    norm = [[m[i][j] / col_sum[j] for j in range(n)] for i in range(n)]
    w = [sum(r) / n for r in norm]
    aw = [sum(m[i][j] * w[j] for j in range(n)) for i in range(n)]
    ratio = [aw[i] / w[i] for i in range(n)]
    lam = sum(ratio) / n
    ci = (lam - n) / (n - 1) if n > 1 else 0
    ri = RI.get(n, 1.59)
    cr = ci / ri if ri else 0
    return {"matrix": m, "col_sum": col_sum, "normalized": norm, "weights": w, "aw": aw, "ratio": ratio, "n": n,
            "lambda_max": lam, "ci": ci, "ri": ri, "cr": cr, "consistent": cr < 0.1}


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
    return str(int(round(v))) if v >= 1 else f"1/{int(round(1 / v))}"


def ahp_example(names, scores, a, i=0, j=1):
    """Contoh perhitungan AHP langkah demi langkah dengan angka nyata. Return list (judul, rumus, substitusi)."""
    n, m, w = a["n"], a["matrix"], a["weights"]
    ci_, cj = names[i], names[j]
    d = scores[i] - scores[j]
    aij = m[i][j]
    col = [m[k][i] for k in range(n)]
    row = a["normalized"][i]
    rule = f"d = {d} ≥ 0 → a = d + 1" if d >= 0 else f"d = {d} < 0 → a = 1/(1 − d)"
    return [
        ("1. Elemen matriks perbandingan",
         "d = sᵢ − sⱼ ;  aᵢⱼ = d + 1 jika d ≥ 0,  aᵢⱼ = 1/(1 − d) jika d < 0  (maks. 9) ;  aⱼᵢ = 1/aᵢⱼ",
         f"{ci_} vs {cj}: d = {scores[i]} − {scores[j]} = {d};  {rule} = {_frac(aij)};  maka a({cj},{ci_}) = {_frac(m[j][i])}"),
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
    col = [r[j] for r in x]
    vcol = [r[j] for r in st["v"]]
    r = st["res"][p]
    cn, pc = names[j], codes[p]
    return [
        ("1. Pembagi normalisasi",
         "√Σᵢ xᵢⱼ²",
         f"Kolom {cn}: √(" + " + ".join(f"{v}²" for v in col) + f") = √{sum(v * v for v in col)} = {_n(st['den'][j])}"),
        ("2. Normalisasi",
         "rᵢⱼ = xᵢⱼ / √Σᵢ xᵢⱼ²",
         f"r({pc},{cn}) = {x[p][j]} / {_n(st['den'][j])} = {_n(st['norm'][p][j])}"),
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


def target_level(score):
    """Konversi skor kebutuhan 1-9 ke target skill skala 1-10."""
    return round(score / 9 * 10)


def analyze(criteria, profiles, players, player_id, target_pos):
    """Analisis lengkap satu pemain.

    criteria : list dict {id, name, training}
    profiles : {pos_index: [skor per kriteria]}
    players  : list dict {id, code, skills: [nilai per kriteria]} (pemain aktif)
    """
    ahps = {p: ahp(profiles[p]) for p in range(len(POSITIONS))}
    idx = next(i for i, pl in enumerate(players) if pl["id"] == player_id)
    mat = [pl["skills"] for pl in players]
    ranking = []
    for p in range(len(POSITIONS)):
        r = topsis(mat, ahps[p]["weights"])[idx]
        ranking.append({"pos": p, "name": POSITIONS[p], **r})
    ranking.sort(key=lambda x: x["ci"], reverse=True)

    w = ahps[target_pos]["weights"]
    skills = players[idx]["skills"]
    gaps = []
    for i, c in enumerate(criteria):
        t = target_level(profiles[target_pos][i])
        g = max(0, t - skills[i])
        gaps.append({"criterion": c["name"], "training": c["training"], "skill": skills[i],
                     "target": t, "gap": g, "weight": w[i], "priority": g * w[i]})
    gaps.sort(key=lambda x: x["priority"], reverse=True)
    fit = 1 - sum(x["priority"] for x in gaps) / (sum(w[i] * target_level(profiles[target_pos][i]) for i in range(len(w))) or 1)
    return {"ranking": ranking, "best": ranking[0], "target": target_pos, "target_name": POSITIONS[target_pos],
            "gaps": gaps, "recommendations": [g for g in gaps if g["gap"] > 0],
            "target_readiness": fit, "target_profile": [target_level(s) for s in profiles[target_pos]]}


def topsis_all(profiles, players):
    """Cᵢ semua pemain untuk semua posisi."""
    mat = [pl["skills"] for pl in players]
    res = {pl["id"]: [] for pl in players}
    for p in range(len(POSITIONS)):
        for pl, r in zip(players, topsis(mat, ahp(profiles[p])["weights"])):
            res[pl["id"]].append(r["ci"])
    return res
