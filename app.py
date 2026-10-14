import os
import random
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

def parse_float(val):
    if val is None or val == '' or val == '-1':
        return None
    try:
        f = float(val)
        return f if f >= 0 else None
    except (ValueError, TypeError):
        return None

def enviar_correo_resultado(correo_destino, nombre_paciente, resultado):
    """
    Envía un correo electrónico formal con el CERTIFICADO CLÍNICO
    y la FICHA TÉCNICA del paciente para el Proyecto de Aula (ABP) - Universidad del Sinú.
    """
    if not correo_destino or '@' not in correo_destino:
        return False, "Correo electrónico no proporcionado o inválido."

    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    remitente = os.getenv('SMTP_FROM', smtp_user or 'noreply@diagnosticodiabetes.com')

    # Datos para el Certificado Diagnóstico
    folio = f"CERT-CLINICO-{datetime.datetime.now().strftime('%Y')}-{random.randint(10000, 99999)}"
    fecha_emision = datetime.datetime.now().strftime("%d/%m/%Y %H:%M hs")
    color = resultado.get('color', '#3b82f6')

    # Formateo de recomendaciones y factores de riesgo
    recs_html = "".join([f"<li>{r}</li>" for r in resultado.get('recomendaciones', [])])
    factores_html = "".join([f"<li>{f}</li>" for f in resultado.get('factores_riesgo', [])])
    factores_section = f"<tr><td colspan='2' style='padding-top:15px;'><strong style='color:#334155;'>Hallazgos / Factores Detectados:</strong><ul style='margin-top:6px;'>{factores_html}</ul></td></tr>" if factores_html else ""

    # Valores Biométricos
    edad_str = f"{int(resultado['edad'])} años" if resultado.get('edad') else "No registrada"
    peso_str = f"{resultado['peso']} kg" if resultado.get('peso') else "No registrado"
    estatura_str = f"{resultado['estatura']} cm" if resultado.get('estatura') else "No registrada"
    imc_str = f"{resultado['imc']} kg/m² ({resultado['imc_categoria']})" if resultado.get('imc') else "No calculado"
    antecedente_fam = "Sí (Padres o Hermanos)" if resultado.get('antecedente_familiar') == 'si' else "No / Desconocido"
    sintomas_str = "Sí (Poliuria, polidipsia o pérdida de peso)" if resultado.get('tiene_sintomas') else "No reporta síntomas severos"

    # Pruebas de Laboratorio
    gpa_str = f"{resultado['gpa']} mg/dL (Límite ≥ 126)" if resultado.get('gpa') is not None else "No evaluada"
    hba1c_str = f"{resultado['hba1c']}% (Límite ≥ 6.5)" if resultado.get('hba1c') is not None else "No evaluada"
    ptog_str = f"{resultado['ptog']} mg/dL (Límite ≥ 200)" if resultado.get('ptog') is not None else "No evaluada"
    casual_str = f"{resultado['casual']} mg/dL (Límite ≥ 200)" if resultado.get('casual') is not None else "No evaluada"

    # Sección HTML de Enfermedades Preexistentes Declaradas (para el certificado)
    enfermedades_previas_lista = resultado.get('enfermedades_previas', [])
    if enfermedades_previas_lista:
        enf_items_html = "".join([
            f"<li style='margin-bottom:5px; padding: 4px 0; border-bottom: 1px solid #f1f5f9;'>"
            f"<span style='color:#dc2626; font-weight:600; margin-right:6px;'>●</span>{e}</li>"
            for e in enfermedades_previas_lista
        ])
        enf_section_html = f"""
        <div class='section-title' style='font-size:13px;font-weight:700;color:#334155;text-transform:uppercase;
            letter-spacing:0.8px;margin-top:25px;margin-bottom:12px;border-bottom:2px solid #e2e8f0;padding-bottom:5px;'>
            🏥 Historial Clínico Previo — Enfermedades Preexistentes Declaradas
        </div>
        <div style='background:#fff5f5; border: 2px solid #fecaca; border-radius:12px; padding:16px 18px; margin-bottom:18px;'>
            <p style='font-size:12px;color:#64748b;margin:0 0 10px 0;'>
                El paciente declaró padecer las siguientes enfermedades o condiciones médicas previas:
            </p>
            <ul style='margin:0; padding-left:20px; font-size:13px; color:#1e293b; line-height:1.6;'>
                {enf_items_html}
            </ul>
            <p style='font-size:11px;color:#94a3b8;margin:10px 0 0 0;font-style:italic;'>
                * Información declarada por el paciente. Debe ser verificada y confirmada por el médico tratante.
            </p>
        </div>
        """
    else:
        enf_section_html = """
        <div class='section-title' style='font-size:13px;font-weight:700;color:#334155;text-transform:uppercase;
            letter-spacing:0.8px;margin-top:25px;margin-bottom:12px;border-bottom:2px solid #e2e8f0;padding-bottom:5px;'>
            🏥 Historial Clínico Previo — Enfermedades Preexistentes Declaradas
        </div>
        <div style='background:#f8fafc; border: 1px dashed #cbd5e1; border-radius:10px; padding:12px 18px; margin-bottom:18px;'>
            <p style='font-size:13px;color:#94a3b8;margin:0;'>
                No se declararon enfermedades preexistentes en esta evaluación.
            </p>
        </div>
        """


    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Certificado de Evaluación Clínica</title>
        <style>
            body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 25px; color: #1e293b; }}
            .cert-card {{ background: #ffffff; max-width: 680px; margin: 0 auto; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; }}
            .cert-header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 28px 30px; color: #ffffff; text-align: center; border-bottom: 5px solid {color}; }}
            .cert-header h1 {{ margin: 0; font-size: 20px; text-transform: uppercase; letter-spacing: 1px; color: #f8fafc; }}
            .cert-header p {{ margin: 6px 0 0 0; font-size: 13px; color: #94a3b8; }}
            .cert-body {{ padding: 30px; }}
            .folio-bar {{ background: #f8fafc; border: 1px dashed #cbd5e1; padding: 10px 18px; border-radius: 10px; font-size: 12px; font-weight: bold; color: #475569; display: flex; justify-content: space-between; margin-bottom: 25px; }}
            
            .section-title {{ font-size: 13px; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 25px; margin-bottom: 12px; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }}
            
            .diag-box {{ background: {color}15; border: 2px solid {color}; border-radius: 14px; padding: 22px; text-align: center; margin-bottom: 22px; }}
            .diag-title {{ font-size: 22px; font-weight: 800; color: {color}; margin: 0 0 6px 0; }}
            .diag-sub {{ font-size: 13px; font-weight: 600; color: #475569; margin: 0; }}
            
            .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 13px; }}
            .info-table td {{ padding: 9px 12px; border-bottom: 1px solid #f1f5f9; }}
            .info-table td.label {{ font-weight: 600; color: #64748b; width: 38%; background: #f8fafc; border-radius: 4px; }}
            .info-table td.value {{ color: #0f172a; font-weight: 500; }}
            
            .motivo-box {{ background: #f8fafc; border-left: 4px solid {color}; padding: 14px 18px; border-radius: 6px; font-size: 13px; line-height: 1.5; color: #334155; margin-bottom: 20px; }}
            
            ul {{ margin: 0; padding-left: 20px; font-size: 13px; color: #334155; line-height: 1.6; }}
            li {{ margin-bottom: 6px; }}
            
            .cert-footer {{ background: #f8fafc; padding: 22px 30px; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; }}
            .stamp {{ font-weight: 700; color: #166534; background: #dcfce7; border: 1px solid #86efac; display: inline-block; padding: 6px 18px; border-radius: 20px; margin-bottom: 12px; }}
        </style>
    </head>
    <body>
        <div class="cert-card">
            <!-- Encabezado del Certificado -->
            <div class="cert-header">
                <h1>📜 Certificado de Evaluación Clínica</h1>
                <p>Proyecto de Aula (ABP) &bull; Universidad del Sinú Elías Bechara Zainúm</p>
            </div>

            <div class="cert-body">
                <!-- Barra de Folio y Fecha -->
                <div class="folio-bar">
                    <span><strong>FOLIO:</strong> {folio}</span>
                    <span><strong>FECHA EMISIÓN:</strong> {fecha_emision}</span>
                </div>

                <!-- Dictamen y Dictamen Diagnóstico -->
                <div class="diag-box">
                    <div class="diag-title">{resultado.get('diagnostico')}</div>
                    <div class="diag-sub">Nivel de Riesgo Clínico: {resultado.get('nivel_riesgo')}</div>
                </div>

                <div class="motivo-box">
                    <strong>Criterio Clínico Aplicado:</strong><br>
                    {resultado.get('motivo')}
                </div>

                <!-- SECCIÓN 1: FICHA TÉCNICA DEL PACIENTE -->
                <div class="section-title">👤 Ficha Técnica e Información del Paciente</div>
                <table class="info-table">
                    <tr>
                        <td class="label">Nombre Completo:</td>
                        <td class="value"><strong>{nombre_paciente}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">Teléfono de Contacto:</td>
                        <td class="value">{resultado.get('telefono') or 'No registrado'}</td>
                    </tr>
                    <tr>
                        <td class="label">Correo Electrónico:</td>
                        <td class="value">{correo_destino}</td>
                    </tr>
                    <tr>
                        <td class="label">Dirección de Hogar:</td>
                        <td class="value">{resultado.get('direccion') or 'No registrada'}</td>
                    </tr>
                    <tr>
                        <td class="label">Antecedentes Médicos:</td>
                        <td class="value">{resultado.get('antecedentes_medicos') or 'Sin registro previo'}</td>
                    </tr>
                    <tr>
                        <td class="label">Edad / Peso / Estatura:</td>
                        <td class="value">{edad_str} | {peso_str} | {estatura_str}</td>
                    </tr>
                    <tr>
                        <td class="label">Índice de Masa Corporal (IMC):</td>
                        <td class="value">{imc_str}</td>
                    </tr>
                    <tr>
                        <td class="label">Antecedentes Familiares:</td>
                        <td class="value">{antecedente_fam}</td>
                    </tr>
                </table>

                <!-- SECCIÓN 1B: ENFERMEDADES PREEXISTENTES DECLARADAS -->
                {enf_section_html}

                <!-- SECCIÓN 2: REGISTRO DE LABORATORIO EVALUADO -->
                <div class="section-title">🧪 Registro de Laboratorio e Indicadores Clínicos</div>
                <table class="info-table">
                    <tr>
                        <td class="label">1. Glucemia en Ayunas (GPa):</td>
                        <td class="value"><strong>{gpa_str}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">2. HbA1c (% Glicosilada):</td>
                        <td class="value"><strong>{hba1c_str}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">3. PTOG 2 Horas:</td>
                        <td class="value"><strong>{ptog_str}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">4. Glucemia Casual / Azar:</td>
                        <td class="value"><strong>{casual_str}</strong></td>
                    </tr>
                    <tr>
                        <td class="label">Síntomas Hiperglucémicos:</td>
                        <td class="value">{sintomas_str}</td>
                    </tr>
                    {factores_section}
                </table>

                <!-- SECCIÓN 3: PLAN DE RECOMENDACIONES -->
                <div class="section-title">📋 Plan y Recomendaciones Médicas Sugeridas</div>
                <ul>
                    {recs_html}
                </ul>
            </div>

            <!-- Pie del Certificado -->
            <div class="cert-footer">
                <div class="stamp">✓ EVALUACIÓN REGISTRADA - PROYECTO ABP 2026</div>
                <p><strong>AVISO ACADÉMICO / MÉDICO:</strong> Este certificado ha sido generado con fines formativos y de orientación preventiva por estudiantes pertenecientes a la <em>Universidad del Sinú Elías Bechara Zainúm</em>. En pacientes asintomáticos con 1 sola prueba alterada en el límite, se requiere confirmación médica formal mediante un segundo estudio de laboratorio en un día diferente.</p>
            </div>
        </div>
    </body>
    </html>
    """

    if not smtp_user or not smtp_password:
        print(f"[DEMO EMAIL] Certificado y Ficha Técnica completos generados para {correo_destino}. (Configure SMTP_USER y SMTP_PASSWORD en su servidor para envío real).")
        return True, f"Certificado y Ficha Técnica procesados para {correo_destino}"

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Certificado de Evaluación Clínica - {nombre_paciente} [{folio}]"
        msg['From'] = remitente
        msg['To'] = correo_destino

        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(remitente, [correo_destino], msg.as_string())

        return True, f"Certificado y Ficha Técnica enviados con éxito a {correo_destino}"
    except Exception as e:
        print(f"[ERROR EMAIL] No se pudo enviar el certificado a {correo_destino}: {e}")
        return False, f"No se pudo enviar el certificado a {correo_destino}: {str(e)}"

def calcular_riesgo_diabetes(datos):
    """
    Evaluación diagnóstica basada en parámetros clínicos de laboratorio y cuadro sintomático:
    - Datos del paciente (Nombre, Teléfono, Correo, Dirección, Antecedentes Médicos)
    - Síntomas de hiperglucemia severa (Poliuria, polidipsia, pérdida de peso)
    - HbA1c (%) -> Límite HbA1c > 3.0% (Validación) / ≥ 6.5% (Diabetes)
    - Glucemia Plasmática en Ayunas (GPa - mg/dL) -> Límite ≥ 126 mg/dL (Diabetes)
    - Prueba de Tolerancia Oral a la Glucosa 2h (PTOG - mg/dL) -> Límite ≥ 200 mg/dL (Diabetes)
    - Glucemia al Azar / Casual (mg/dL) -> Límite ≥ 200 mg/dL (Diabetes)
    """
    nombre = datos.get('nombre', 'Paciente').strip() or 'Paciente'
    telefono = datos.get('telefono', '').strip()
    correo = datos.get('correo', '').strip()
    direccion = datos.get('direccion', '').strip()
    antecedentes_medicos = datos.get('antecedentes_medicos', '').strip()
    tiene_sintomas = str(datos.get('tiene_sintomas', '')).lower() in ['true', 'si', 's', '1', 'on']

    # Enfermedades preexistentes declaradas (puede venir como lista JSON o string separado por comas)
    enfermedades_raw = datos.get('enfermedades_previas', [])
    if isinstance(enfermedades_raw, list):
        enfermedades_previas = [e.strip() for e in enfermedades_raw if e.strip()]
    elif isinstance(enfermedades_raw, str) and enfermedades_raw.strip():
        enfermedades_previas = [e.strip() for e in enfermedades_raw.split(',') if e.strip()]
    else:
        enfermedades_previas = []

    # Captura de pruebas de laboratorio
    gpa = parse_float(datos.get('gpa') or datos.get('glucosa'))
    hba1c = parse_float(datos.get('hba1c'))
    ptog = parse_float(datos.get('ptog'))
    casual = parse_float(datos.get('casual'))

    # Al menos una prueba debe ser proporcionada
    if gpa is None and hba1c is None and ptog is None and casual is None:
        return {'error': 'Debes ingresar al menos el valor de una prueba de laboratorio (Glucosa en ayunas, HbA1c, PTOG o Glucosa casual).'}

    # Validación de límites fisiológicos (HbA1c > 3.0%)
    for valor, nombre_p in [(gpa, 'Glucosa en Ayunas'), (casual, 'Glucosa Casual'), (ptog, 'PTOG')]:
        if valor is not None and valor > 700:
            return {'error': f'El valor de {nombre_p} ({valor} mg/dL) está fuera de límites plausibles.'}
    if hba1c is not None and (hba1c < 3.0 or hba1c > 20.0):
        return {'error': f'El valor de HbA1c ({hba1c}%) está fuera de límites plausibles (debe ser mayor a 3.0% y hasta 20.0%).'}

    # Evaluación de criterios positivos para Diabetes
    pos_hba1c = hba1c is not None and hba1c >= 6.5
    pos_gpa = gpa is not None and gpa >= 126.0
    pos_ptog = ptog is not None and ptog >= 200.0
    pos_casual = casual is not None and casual >= 200.0

    # Evaluación de Prediabetes
    pre_hba1c = hba1c is not None and (5.7 <= hba1c <= 6.4)
    pre_gpa = gpa is not None and (100.0 <= gpa <= 125.0)
    pre_ptog = ptog is not None and (140.0 <= ptog <= 199.0)

    # Conteo de pruebas de laboratorio positivas
    pruebas_positivas = sum([pos_hba1c, pos_gpa, pos_ptog])

    # Lógica Diagnóstica (Implementando la regla clínica institucional)
    if tiene_sintomas and pos_casual:
        diagnostico = "DIABETES MELLITUS CONFIRMADA"
        categoria_codigo = "diabetes"
        nivel_riesgo = "Confirmado / Atención Médica Urgente"
        color = "#ef4444"
        motivo = "Paciente con síntomas claros de hiperglucemia severa y glucemia al azar ≥ 200 mg/dL."
        recomendaciones = [
            "Es imperativo consultar de inmediato a un médico especialista (Endocrinólogo).",
            "Iniciar protocolo de manejo metabólico y evaluación de laboratorios integrales.",
            "Mantener hidratación constante y acudir a un centro de atención clínica urgente."
        ]
        porcentaje_medidor = 95

    elif tiene_sintomas and (pos_hba1c or pos_gpa or pos_ptog):
        diagnostico = "DIABETES MELLITUS CONFIRMADA"
        categoria_codigo = "diabetes"
        nivel_riesgo = "Confirmado / Requiere Tratamiento"
        color = "#ef4444"
        motivo = "Paciente sintomático con al menos una prueba de laboratorio en rango diagnóstico de diabetes (GPa ≥ 126 mg/dL, HbA1c ≥ 6.5% o PTOG ≥ 200 mg/dL)."
        recomendaciones = [
            "Acudir de inmediato a consulta médica para valoración formal e inicio de plan terapéutico.",
            "Realizar monitoreo continuo de glucemia y evaluación renal/cardiovascular.",
            "Recibir orientación de educación en diabetes y plan nutricional personalizado."
        ]
        porcentaje_medidor = 90

    elif not tiene_sintomas and pruebas_positivas >= 2:
        diagnostico = "DIABETES MELLITUS CONFIRMADA"
        categoria_codigo = "diabetes"
        nivel_riesgo = "Confirmado (Criterio Multilaboratorio)"
        color = "#ef4444"
        motivo = "Paciente asintomático pero con 2 o más pruebas distintas alteradas en la misma evaluación (criterio confirmatorio concordante)."
        recomendaciones = [
            "Confirmación concordante entre pruebas distintas. Requiere consulta médica a la brevedad.",
            "Evaluación de hábitos de estilo de vida, perfil lipídico y función metabólica.",
            "Seguimiento especializado continuo."
        ]
        porcentaje_medidor = 85

    elif not tiene_sintomas and (pruebas_positivas == 1 or pos_casual):
        diagnostico = "RESULTADO POSITIVO PRELIMINAR"
        categoria_codigo = "preliminar"
        nivel_riesgo = "Elevado / Requiere Confirmación"
        color = "#f97316"
        motivo = "Al no presentar síntomas claros de hiperglucemia severa y tener solo 1 prueba alterada en el límite crítico (GPa ≥ 126 mg/dL, HbA1c ≥ 6.5% o PTOG/Casual ≥ 200 mg/dL), las pautas clínicas exigen repetir la prueba para confirmar."
        recomendaciones = [
            "No entrar en pánico: Al ser asintomático con una única prueba alterada, se debe REPETIR la prueba alterada en un día diferente para confirmar.",
            "Agendar consulta médica para programar la prueba de confirmación de laboratorio.",
            "Adopta medidas preventivas inmediatas en tu dieta reduciendo carbohidratos simples y azúcares."
        ]
        porcentaje_medidor = 78

    elif pre_hba1c or pre_gpa or pre_ptog:
        diagnostico = "PREDIABETES (Riesgo Elevado)"
        categoria_codigo = "prediabetes"
        nivel_riesgo = "Moderado / Intermedio"
        color = "#f59e0b"
        motivo = "Presenta valores en rango de alteración intermedia (HbA1c 5.7-6.4%, Glucosa ayunas 100-125 mg/dL o PTOG 140-199 mg/dL)."
        recomendaciones = [
            "La prediabetes se puede revertir con cambios en el estilo de vida.",
            "Reducir consumo de harinas refinadas, bebidas azucaradas y ultraprocesados.",
            "Realizar al menos 150 minutos a la semana de ejercicio aeróbico y de fuerza.",
            "Repetir controles de glucemia anualmente."
        ]
        porcentaje_medidor = 60

    else:
        diagnostico = "VALORES NORMALES"
        categoria_codigo = "normal"
        nivel_riesgo = "Bajo"
        color = "#10b981"
        motivo = "Ninguna de las pruebas ingresadas supera los umbrales clínicos de prediabetes ni diabetes."
        recomendaciones = [
            "Mantén un estilo de vida activo y alimentación balanceada.",
            "Realiza chequeos médicos preventivos de rutina una vez al año."
        ]
        porcentaje_medidor = 35

    # Determinación de Nivel Crítico / Alerta (Activado para Diabetes y Prediabetes)
    es_critico = categoria_codigo in ['diabetes', 'preliminar', 'prediabetes']

    # Evaluación de IMC y otros factores
    peso = parse_float(datos.get('peso'))
    estatura = parse_float(datos.get('estatura'))
    imc = None
    imc_categoria = None
    if peso and estatura:
        estatura_m = estatura / 100.0 if estatura > 3.0 else estatura
        if 0.5 <= estatura_m <= 2.5 and 20 <= peso <= 300:
            imc = round(peso / (estatura_m ** 2), 1)
            if imc < 18.5: imc_categoria = "Bajo peso"
            elif 18.5 <= imc < 25.0: imc_categoria = "Peso normal"
            elif 25.0 <= imc < 30.0: imc_categoria = "Sobrepeso"
            else: imc_categoria = "Obesidad"

    factores_riesgo = []
    if tiene_sintomas:
        factores_riesgo.append("Presencia de síntomas clásicos (Poliuria, polidipsia, pérdida de peso)")
    if pos_hba1c: factores_riesgo.append(f"HbA1c en rango diabetes: {hba1c}% (≥ 6.5%)")
    elif pre_hba1c: factores_riesgo.append(f"HbA1c en prediabetes: {hba1c}% (5.7% - 6.4%)")
    if pos_gpa: factores_riesgo.append(f"Glucosa ayunas (GPa) en rango límite crítico: {gpa} mg/dL (≥ 126 mg/dL)")
    elif pre_gpa: factores_riesgo.append(f"Glucosa ayunas (GPa) en prediabetes: {gpa} mg/dL (100 - 125 mg/dL)")
    if pos_ptog: factores_riesgo.append(f"PTOG 2h en rango límite crítico: {ptog} mg/dL (≥ 200 mg/dL)")
    elif pre_ptog: factores_riesgo.append(f"PTOG 2h en prediabetes: {ptog} mg/dL (140 - 199 mg/dL)")
    if pos_casual: factores_riesgo.append(f"Glucosa casual en rango límite crítico: {casual} mg/dL (≥ 200 mg/dL)")
    # Agregar enfermedades preexistentes declaradas como factores adicionales
    for enfermedad in enfermedades_previas:
        factores_riesgo.append(f"Antecedente declarado: {enfermedad}")

    if imc:
        factores_riesgo.append(f"IMC: {imc} kg/m² ({imc_categoria})")
    if datos.get('antecedente') == 'si':
        factores_riesgo.append("Antecedentes familiares directos de diabetes")
    if datos.get('actividad') == 'sedentario':
        factores_riesgo.append("Estilo de vida sedentario")

    val_mostrar = gpa or casual or ptog or (hba1c if hba1c else "--")

    return {
        'nombre': nombre,
        'telefono': telefono,
        'correo': correo,
        'direccion': direccion,
        'antecedentes_medicos': antecedentes_medicos,
        'enfermedades_previas': enfermedades_previas,
        'glucosa': val_mostrar,
        'diagnostico': diagnostico,
        'categoria_codigo': categoria_codigo,
        'nivel_riesgo': nivel_riesgo,
        'color': color,
        'motivo': motivo,
        'recomendaciones': recomendaciones,
        'porcentaje_medidor': porcentaje_medidor,
        'tiene_sintomas': tiene_sintomas,
        'hba1c': hba1c,
        'gpa': gpa,
        'ptog': ptog,
        'casual': casual,
        'edad': parse_float(datos.get('edad')),
        'peso': peso,
        'estatura': estatura,
        'antecedente_familiar': datos.get('antecedente', 'no'),
        'imc': imc,
        'imc_categoria': imc_categoria,
        'factores_riesgo': factores_riesgo,
        'es_critico': es_critico
    }

# ==============================================================================
# BASE DE DATOS Y MOTOR DE INTELIGENCIA ARTIFICIAL PARA DETECCIÓN DE COMIDAS
# ==============================================================================
DICCIONARIO_ALIMENTOS = {
    'bandeja_paisa': {
        'nombre': 'Bandeja Paisa Tradicional',
        'ingredientes': ['Frijoles rojos', 'Arroz blanco', 'Chicharrón', 'Carne molida', 'Huevo frito', 'Plátano maduro', 'Arepa', 'Aguacate'],
        'calorias': 980, 'carbohidratos': 92, 'proteinas': 46, 'grasas': 50,
        'indice_glucemico': 'Alto (78)', 'carga_glucemica': 'Alta (71.8)',
        'impacto_glucosa': '+75 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Alta concentración de carbohidratos simples y grasas saturadas. Genera pico hiperglucémico severo y prolongado.'
    },
    'arroz_pollo': {
        'nombre': 'Arroz con Pollo y Ensalada Mixta',
        'ingredientes': ['Arroz blanco sazonado', 'Pechuga de pollo desmechada', 'Zanahoria', 'Arvejas', 'Habichuela', 'Ensalada de lechuga y tomate'],
        'calorias': 520, 'carbohidratos': 62, 'proteinas': 34, 'grasas': 15,
        'indice_glucemico': 'Medio (62)', 'carga_glucemica': 'Media (38.4)',
        'impacto_glucosa': '+42 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'La fibra de las verduras modera la absorción de los almidones del arroz blanco.'
    },
    'pescado_frito': {
        'nombre': 'Pescado Frito con Patacones y Arroz de Coco',
        'ingredientes': ['Mojarra o corvina frita', 'Arroz con coco', 'Patacones de plátano verde', 'Ensalada de aguacate'],
        'calorias': 780, 'carbohidratos': 74, 'proteinas': 38, 'grasas': 36,
        'indice_glucemico': 'Alto (74)', 'carga_glucemica': 'Alta (54.8)',
        'impacto_glucosa': '+65 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'La combinación de fritura con almidones densos incrementa la resistencia transitoria a la insulina.'
    },
    'pechuga_plancha': {
        'nombre': 'Pechuga a la Plancha con Puré y Brócoli al Vapor',
        'ingredientes': ['Pechuga de pollo a la plancha', 'Brócoli y zanahoria al vapor', 'Puré de papa casero', 'Aceite de oliva virgen'],
        'calorias': 410, 'carbohidratos': 28, 'proteinas': 44, 'grasas': 12,
        'indice_glucemico': 'Bajo (38)', 'carga_glucemica': 'Baja (10.6)',
        'impacto_glucosa': '+22 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Excelente opción metabólica: alta proteína magra y fibra vegetal que estabilizan la glucemia sin picos severos.'
    },
    'arepa_queso_huevo': {
        'nombre': 'Arepa de Maíz con Huevo y Queso Costeño',
        'ingredientes': ['Arepa de maíz blanco asada', 'Huevo revuelto o perico', 'Queso blanco bajo en sal'],
        'calorias': 340, 'carbohidratos': 34, 'proteinas': 18, 'grasas': 14,
        'indice_glucemico': 'Medio (56)', 'carga_glucemica': 'Media (19.0)',
        'impacto_glucosa': '+30 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Desayuno balanceado. Para reducir el índice glucémico se recomienda añadir semillas de chía o avena a la masa.'
    },
    'avena_fruta': {
        'nombre': 'Avena en Hojuelas con Fruta Fresca y Semillas',
        'ingredientes': ['Avena entera cocida en agua o leche descremada', 'Rodajas de manzana o fresas', 'Canela', 'Semillas de chía'],
        'calorias': 270, 'carbohidratos': 42, 'proteinas': 11, 'grasas': 5,
        'indice_glucemico': 'Bajo (44)', 'carga_glucemica': 'Baja (18.5)',
        'impacto_glucosa': '+24 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Los betaglucanos de la avena ralentizan la absorción de carbohidratos y favorecen el control glucémico.'
    },
    'sopa_verduras': {
        'nombre': 'Sopa Casera de Verduras con Pollo',
        'ingredientes': ['Caldo desgrasado', 'Pechuga de pollo', 'Calabacín', 'Espinaca', 'Zanahoria', 'Apio'],
        'calorias': 210, 'carbohidratos': 16, 'proteinas': 24, 'grasas': 5,
        'indice_glucemico': 'Bajo (32)', 'carga_glucemica': 'Baja (5.1)',
        'impacto_glucosa': '+15 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Ideal para la cena: bajo impacto nocturno, previene elevaciones anormales de glucemia en ayunas a la mañana siguiente.'
    },
    'hamburguesa_papas': {
        'nombre': 'Hamburguesa con Queso y Papas Fritas',
        'ingredientes': ['Pan blanco refinado', 'Carne molida', 'Queso cheddar', 'Salsas azucaradas', 'Papas fritas'],
        'calorias': 890, 'carbohidratos': 84, 'proteinas': 36, 'grasas': 46,
        'indice_glucemico': 'Alto (82)', 'carga_glucemica': 'Muy Alta (68.9)',
        'impacto_glucosa': '+78 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Alimento ultraprocesado crítico. El almidón refinado y las grasas retardan el vaciado gástrico prolongando la hiperglucemia por más de 4 horas.'
    },
    'pizza': {
        'nombre': 'Pizza Clásica de Jamón y Queso (2 Porciones)',
        'ingredientes': ['Masa de harina de trigo refinada', 'Salsa de tomate', 'Queso mozzarella', 'Jamón'],
        'calorias': 590, 'carbohidratos': 68, 'proteinas': 26, 'grasas': 24,
        'indice_glucemico': 'Alto (76)', 'carga_glucemica': 'Alta (51.7)',
        'impacto_glucosa': '+60 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Carbohidratos de rápida absorción combinados con grasas producen picos tardíos sostenidos.'
    },
    'ensalada_cesar': {
        'nombre': 'Ensalada César con Pollo a la Parrilla',
        'ingredientes': ['Lechuga romana fresca', 'Pechuga de pollo asada', 'Queso parmesano', 'Crutones integrales ligeros', 'Aderezo de yogur'],
        'calorias': 370, 'carbohidratos': 14, 'proteinas': 35, 'grasas': 18,
        'indice_glucemico': 'Bajo (28)', 'carga_glucemica': 'Baja (3.9)',
        'impacto_glucosa': '+14 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Excelente para el control metabólico: el impacto en la curva glucémica es mínimo y proporciona saciedad prolongada.'
    },
    'sancocho': {
        'nombre': 'Sancocho Tradicional de Res y Gallina',
        'ingredientes': ['Carne de res o gallina', 'Plátano verde', 'Yuca', 'Mazorca', 'Papa', 'Cilantro'],
        'calorias': 690, 'carbohidratos': 66, 'proteinas': 40, 'grasas': 28,
        'indice_glucemico': 'Medio-Alto (68)', 'carga_glucemica': 'Alta (44.9)',
        'impacto_glucosa': '+52 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Contiene múltiples fuentes de almidón (yuca, plátano, papa y mazorca). Se sugiere reducir a 1 sola porción de almidón.'
    },
    'yogur_frutos_secos': {
        'nombre': 'Yogur Griego Natural con Frutos Secos',
        'ingredientes': ['Yogur griego sin azúcar', 'Almendras', 'Nueces', 'Semillas de lino'],
        'calorias': 210, 'carbohidratos': 11, 'proteinas': 18, 'grasas': 11,
        'indice_glucemico': 'Muy Bajo (22)', 'carga_glucemica': 'Baja (2.4)',
        'impacto_glucosa': '+10 mg/dL en pico postprandial a las 2 horas',
        'advertencia': 'Snack óptimo: bajo índice glucémico y grasas monoinsaturadas cardiosaludables que mejoran la sensibilidad insulínica.'
    }
}

def ia_analizar_alimento(datos):
    """
    Simulación de análisis por Inteligencia Artificial de alimentos:
    Identifica el plato, estima calorías, macronutrientes, índice glucémico
    y calcula el impacto metabólico en la glucosa en sangre.
    """
    id_plato = datos.get('id_plato', '').strip().lower()
    nombre_plato = datos.get('nombre_plato', '').strip()
    
    calorias_custom = parse_float(datos.get('calorias') or datos.get('calorias_custom'))

    # 1. Búsqueda directa por ID o clave
    if id_plato in DICCIONARIO_ALIMENTOS:
        item = dict(DICCIONARIO_ALIMENTOS[id_plato])
        item['id'] = id_plato
        if calorias_custom and calorias_custom > 0:
            item['calorias'] = int(calorias_custom)
            item['carbohidratos'] = round(calorias_custom * 0.12, 1)
        return item

    # 2. Búsqueda por coincidencia en texto (insensible a acentos y espacios)
    busqueda = (nombre_plato or id_plato).lower().strip()
    busq_norm = busqueda.replace(' ', '_')
    for key, item in DICCIONARIO_ALIMENTOS.items():
        nom_item = item['nombre'].lower()
        if (key in busq_norm or busq_norm in key or
            busqueda in nom_item or nom_item in busqueda or
            all(k in busqueda for k in key.split('_') if len(k) > 3) or
            any(ing.lower() in busqueda for ing in item['ingredientes'])):
            res = dict(item)
            res['id'] = key
            if calorias_custom and calorias_custom > 0:
                res['calorias'] = int(calorias_custom)
                res['carbohidratos'] = round(calorias_custom * 0.12, 1)
            return res

    # 3. Estimación inteligente para CUALQUIER comida personalizada que el usuario ingrese
    
    # Análisis granular de palabras clave
    calorias_est = 380
    carbs_est = 42
    prot_est = 22
    grasas_est = 14
    ig_est = 'Medio (52)'
    impacto_mg = 32

    # Reglas nutricionales combinadas
    es_frito_o_chatarra = any(k in busqueda for k in ['frit', 'hamburgues', 'pizza', 'papas frit', 'empanad', 'gaseos', 'dulce', 'postre', 'chicharron', 'perro caliente'])
    es_proteina_magra = any(k in busqueda for k in ['pechuga', 'pollo', 'carne', 'lomo', 'pescado', 'atun', 'salmon', 'huevo', 'claras'])
    es_almidon_o_carbo = any(k in busqueda for k in ['arroz', 'yuca', 'platano', 'papa', 'mazorca', 'pasta', 'espagueti', 'frijol', 'lenteja', 'pan', 'arepa', 'tajad'])
    es_vegetal_o_ligero = any(k in busqueda for k in ['ensalada', 'verdura', 'sopa', 'caldo', 'crema', 'espinaca', 'brocoli', 'tomate', 'lechuga', 'yogur', 'fruta'])

    if es_frito_o_chatarra:
        calorias_est = 740
        carbs_est = 76
        prot_est = 24
        grasas_est = 38
        ig_est = 'Alto (78)'
        impacto_mg = 68
        adv = 'Comida con alta densidad calórica y grasas/azúcares. Se aconseja moderar la porción para evitar picos hiperglucémicos.'
    elif es_vegetal_o_ligero and not es_almidon_o_carbo:
        calorias_est = 220
        carbs_est = 16
        prot_est = 18
        grasas_est = 6
        ig_est = 'Bajo (32)'
        impacto_mg = 16
        adv = 'Plato liviano favorable: bajo impacto glucémico, rico en micronutrientes y fibra protectora.'
    elif es_proteina_magra and not es_almidon_o_carbo:
        calorias_est = 340
        carbs_est = 10
        prot_est = 42
        grasas_est = 12
        ig_est = 'Muy Bajo (25)'
        impacto_mg = 12
        adv = 'Aporte proteico magro que estabiliza la respuesta de la insulina sin elevar abruptamente la glucemia.'
    elif es_almidon_o_carbo:
        calorias_est = 520
        carbs_est = 64
        prot_est = 26
        grasas_est = 16
        ig_est = 'Medio-Alto (64)'
        impacto_mg = 46
        adv = 'Contiene fuentes de carbohidratos complejos. Acompañar con ensalada y agua para ralentizar la absorción de glucosa.'
    else:
        adv = 'Estimación analítica adaptada a tu porción declarada.'

    # Si el usuario especificó sus propias calorías, se respetan estrictamente
    if calorias_custom and calorias_custom > 0:
        calorias_est = int(calorias_custom)
        carbs_est = round(calorias_est * 0.12, 1)
        prot_est = round(calorias_est * 0.06, 1)
        grasas_est = round(calorias_est * 0.035, 1)

    nombre_formateado = nombre_plato.strip().capitalize() if nombre_plato else 'Comida Personalizada'
    return {
        'id': 'personalizado',
        'nombre': nombre_formateado,
        'ingredientes': [nombre_formateado, 'Ingredientes declarados por el usuario'],
        'calorias': calorias_est,
        'carbohidratos': carbs_est,
        'proteinas': prot_est,
        'grasas': grasas_est,
        'indice_glucemico': ig_est,
        'carga_glucemica': f'Estimada ({round(carbs_est * 0.55, 1)})',
        'impacto_glucosa': f'+{impacto_mg} mg/dL en pico postprandial a las 2 horas',
        'advertencia': adv
    }

# ==============================================================================
# MOTOR NLP: EXTRACCIÓN DE SÍNTOMAS DESDE EL AUDIO/VOZ DEL PACIENTE
# ==============================================================================
PATRONES_SINTOMAS = [
    {
        'id': 'polidipsia',
        'nombre': 'Polidipsia (Sed excesiva / Sed insaciable)',
        'tipo': 'cardinal',
        'palabras': ['sed', 'mucha sed', 'sedienta', 'sediento', 'agua todo el dia', 'boca seca', 'tomando agua', 'sed constante', 'tomo mucha agua']
    },
    {
        'id': 'poliuria',
        'nombre': 'Poliuria (Micción frecuente / Orinar mucho)',
        'tipo': 'cardinal',
        'palabras': ['orina', 'orinar', 'orino', 'baño', 'miccion', 'ganas de orinar', 'noche al bano', 'orino a cada rato', 'orino mucho']
    },
    {
        'id': 'polifagia',
        'nombre': 'Polifagia (Hambre excesiva / Ansiedad por comer)',
        'tipo': 'cardinal',
        'palabras': ['hambre', 'mucha hambre', 'comer', 'apetito', 'ansiedad por comer', 'hambre todo el tiempo']
    },
    {
        'id': 'perdida_peso',
        'nombre': 'Pérdida de peso involuntaria o inexplicable',
        'tipo': 'cardinal',
        'palabras': ['baje de peso', 'rebaje', 'perdida de peso', 'perdiendo peso', 'adelgace', 'flaco', 'delgado de repente']
    },
    {
        'id': 'fatiga',
        'nombre': 'Fatiga extrema y debilidad general',
        'tipo': 'secundario',
        'palabras': ['cansancio', 'cansado', 'agotado', 'fatiga', 'sin energia', 'sueno todo el dia', 'debil', 'agotamiento']
    },
    {
        'id': 'vision_borrosa',
        'nombre': 'Visión borrosa o dificultad de enfoque',
        'tipo': 'secundario',
        'palabras': ['vision', 'veo borroso', 'vista nublada', 'borrosa', 'ojos nublados', 'dificultad para ver']
    },
    {
        'id': 'hormigueo',
        'nombre': 'Hormigueo o entumecimiento en pies y manos',
        'tipo': 'secundario',
        'palabras': ['hormigueo', 'adormecimiento', 'pies dormidos', 'manos dormidas', 'pinchazos', 'ardor en los pies']
    },
    {
        'id': 'cicatrizacion_lenta',
        'nombre': 'Cicatrización lenta de heridas o infecciones recurrentes',
        'tipo': 'secundario',
        'palabras': ['heridas', 'cicatrizar', 'no sana', 'llagas', 'infeccion', 'demora en sanar']
    }
]

def extraer_sintomas_de_texto(texto):
    """
    Analiza la transcripción del audio de la voz del paciente para detectar
    síntomas clínicos estructurados de Diabetes Mellitus.
    """
    if not texto:
        return []

    texto_clean = texto.lower()
    for orig, rep in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ñ', 'n')]:
        texto_clean = texto_clean.replace(orig, rep)

    encontrados = []
    for patron in PATRONES_SINTOMAS:
        for termino in patron['palabras']:
            termino_clean = termino.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            if termino_clean in texto_clean:
                encontrados.append({
                    'id': patron['id'],
                    'nombre': patron['nombre'],
                    'tipo': patron['tipo'],
                    'coincidencia': termino
                })
                break
    return encontrados

# ==============================================================================
# MOTOR CLÍNICO PREDICTIVO INTEGRAL (SIN REQUERIR GLUCÓMETRO PREVIO)
# ==============================================================================
def evaluar_riesgo_sin_laboratorio(datos):
    """
    Evalúa el estado metabólico y proyecta el reporte del glucómetro del paciente
    integrando:
    1. Datos del paciente y antecedentes (Opción 1)
    2. Síntomas registrados por audio/voz (Opción 1)
    3. Registro semanal de comidas y calorías (Opción 2)
    4. Alimentos detectados por IA (Opción 3)

    OJO: El paciente NO conoce su nivel de glucosa en sangre previamente;
    el sistema formula el diagnóstico orientativo, calcula su curva glucémica
    y emite la ficha técnica / térmica institucional imprimible en PDF.
    """
    nombre = datos.get('nombre', 'Paciente').strip() or 'Paciente'
    telefono = datos.get('telefono', '').strip()
    correo = datos.get('correo', '').strip()
    direccion = datos.get('direccion', '').strip()
    edad = parse_float(datos.get('edad')) or 35.0
    peso = parse_float(datos.get('peso')) or 70.0
    estatura = parse_float(datos.get('estatura')) or 170.0
    genero = datos.get('genero', 'no_especificado')
    antecedente_familiar = datos.get('antecedente_familiar', 'no')
    actividad = datos.get('actividad', 'moderado')
    antecedentes_medicos = datos.get('antecedentes_medicos', '').strip()

    # Cálculo antropométrico de IMC
    estatura_m = estatura / 100.0 if estatura > 3.0 else estatura
    imc = round(peso / (estatura_m ** 2), 1) if (estatura_m > 0.5 and peso > 20) else 24.2
    if imc < 18.5:
        imc_categoria = "Bajo peso"
        imc_color = "#38bdf8"
    elif 18.5 <= imc < 25.0:
        imc_categoria = "Peso saludable"
        imc_color = "#10b981"
    elif 25.0 <= imc < 30.0:
        imc_categoria = "Sobrepeso"
        imc_color = "#f59e0b"
    else:
        imc_categoria = "Obesidad"
        imc_color = "#ef4444"

    # Procesamiento de Síntomas (Seleccionados + Detectados en Audio)
    sintomas_lista = datos.get('sintomas', [])
    if isinstance(sintomas_lista, str):
        sintomas_lista = [s.strip() for s in sintomas_lista.split(',') if s.strip()]

    transcripcion_audio = datos.get('audio_transcripcion', '').strip()
    sintomas_voz = extraer_sintomas_de_texto(transcripcion_audio)
    for sv in sintomas_voz:
        if sv['id'] not in sintomas_lista:
            sintomas_lista.append(sv['id'])

    # Métricas Nutricionales y Calóricas Semanales (Opción 2)
    calorias_semana = parse_float(datos.get('calorias_semana_total')) or 14000.0
    calorias_promedio_dia = parse_float(datos.get('calorias_promedio_dia')) or round(calorias_semana / 7.0, 0)
    carbohidratos_promedio = parse_float(datos.get('carbohidratos_promedio')) or 220.0
    dias_registrados = int(datos.get('dias_registrados') or 7)

    # Gasto Energético Total Estimado
    tmb = (10 * peso) + (6.25 * (estatura_m * 100)) - (5 * edad) + (5 if genero == 'masculino' else -161)
    factor_act = 1.2 if actividad == 'sedentario' else (1.55 if actividad == 'activo' else 1.375)
    calorias_meta_dia = round(tmb * factor_act, 0)
    balance_calorico = round(calorias_promedio_dia - calorias_meta_dia, 0)

    # Score FINDRISC adaptado
    score = 0
    factores_detectados = []

    # 1. Edad
    if edad < 45: score += 0
    elif edad <= 54:
        score += 2
        factores_detectados.append(f"Edad en rango de riesgo moderado ({int(edad)} años)")
    elif edad <= 64:
        score += 3
        factores_detectados.append(f"Edad en rango de riesgo elevado ({int(edad)} años)")
    else:
        score += 4
        factores_detectados.append(f"Edad mayor a 64 años ({int(edad)} años)")

    # 2. IMC
    if imc >= 30.0:
        score += 3
        factores_detectados.append(f"Obesidad clínica (IMC {imc} kg/m²)")
    elif imc >= 25.0:
        score += 1
        factores_detectados.append(f"Sobrepeso (IMC {imc} kg/m²)")

    # 3. Antecedente familiar
    if antecedente_familiar in ['si', 'padres', 'hermanos', 'directo']:
        score += 5
        factores_detectados.append("Antecedente familiar directo de Diabetes (Padres o Hermanos)")
    elif antecedente_familiar in ['abuelos', 'tios']:
        score += 3
        factores_detectados.append("Antecedente familiar de 2° grado de Diabetes (Abuelos o Tíos)")

    # 4. Actividad física
    if actividad == 'sedentario':
        score += 2
        factores_detectados.append("Estilo de vida sedentario (< 30 min de actividad diaria)")

    # 5. Sobrecarga calórica
    if balance_calorico > 400 or carbohidratos_promedio > 300:
        score += 3
        factores_detectados.append(f"Superávit calórico y dieta alta en carbohidratos ({int(calorias_promedio_dia)} kcal/día promedio)")
    elif balance_calorico > 150 or carbohidratos_promedio > 250:
        score += 1
        factores_detectados.append("Ingesta calórica ligeramente superior a la meta recomendada")

    # 6. Síntomas clásicos de hiperglucemia
    sintomas_cardinales_ids = ['polidipsia', 'poliuria', 'polifagia', 'perdida_peso']
    cardinales_presentes = [s for s in sintomas_lista if any(cid in s.lower() for cid in sintomas_cardinales_ids)]
    if cardinales_presentes:
        score += len(cardinales_presentes) * 3
        nombres_sint = []
        for c in cardinales_presentes:
            if 'polidipsia' in c: nombres_sint.append("Polidipsia (Mucha sed)")
            elif 'poliuria' in c: nombres_sint.append("Poliuria (Orinar con frecuencia)")
            elif 'polifagia' in c: nombres_sint.append("Polifagia (Hambre insaciable)")
            elif 'perdida_peso' in c: nombres_sint.append("Pérdida de peso inexplicable")
        factores_detectados.append(f"Presencia de síntomas cardinales de alarma: {', '.join(nombres_sint)}")

    # 7. Síntomas secundarios
    secundarios_ids = ['fatiga', 'vision_borrosa', 'hormigueo', 'cicatrizacion_lenta']
    secundarios_presentes = [s for s in sintomas_lista if any(sid in s.lower() for sid in secundarios_ids)]
    if secundarios_presentes:
        score += len(secundarios_presentes) * 1.5
        factores_detectados.append(f"Síntomas complementarios declarados ({len(secundarios_presentes)} síntomas)")

    if antecedentes_medicos:
        factores_detectados.append(f"Historial médico previo: {antecedentes_medicos}")

    # Clasificación y Proyección de Glucosa
    if score < 7:
        basal = round(82.0 + (score * 1.8), 0)
        diagnostico = "VALORES ESTIMADOS EN RANGO NORMAL / SALUDABLE"
        categoria_codigo = "normal"
        nivel_riesgo = "Bajo Riesgo Metabólico"
        color = "#10b981"
        porcentaje_medidor = max(20, min(40, int(score * 4 + 15)))
    elif score <= 12:
        basal = round(98.0 + ((score - 7) * 2.5), 0)
        diagnostico = "RIESGO MODERADO - SOSPECHA DE PREDIABETES"
        categoria_codigo = "prediabetes"
        nivel_riesgo = "Riesgo Moderado"
        color = "#f59e0b"
        porcentaje_medidor = max(45, min(65, int(score * 4 + 18)))
    elif score <= 18:
        basal = round(114.0 + ((score - 12) * 2.5), 0)
        diagnostico = "RIESGO ELEVADO DE PREDIABETES / DIABETES TEMPRANA"
        categoria_codigo = "preliminar"
        nivel_riesgo = "Riesgo Elevado / Requiere Confirmación"
        color = "#f97316"
        porcentaje_medidor = max(68, min(82, int(score * 3.5 + 20)))
    else:
        basal = round(130.0 + min(65.0, (score - 18) * 3.2), 0)
        diagnostico = "ALTO RIESGO CLÍNICO DE DIABETES MELLITUS"
        categoria_codigo = "diabetes"
        nivel_riesgo = "Alto / Atención Médica Urgente"
        color = "#ef4444"
        porcentaje_medidor = max(85, min(98, int(score * 2.5 + 40)))

    factor_pico_desayuno = 32.0 if carbohidratos_promedio < 200 else (45.0 if carbohidratos_promedio < 280 else 60.0)
    factor_pico_almuerzo = 40.0 if carbohidratos_promedio < 200 else (55.0 if carbohidratos_promedio < 280 else 75.0)
    factor_pico_cena = 28.0 if carbohidratos_promedio < 200 else (38.0 if carbohidratos_promedio < 280 else 52.0)

    mult_resistencia = 1.0 if score < 7 else (1.2 if score <= 12 else (1.4 if score <= 18 else 1.65))

    pico_desayuno = round(basal + (factor_pico_desayuno * mult_resistencia), 0)
    pre_almuerzo = round(basal + (8.0 * mult_resistencia), 0)
    pico_almuerzo = round(basal + (factor_pico_almuerzo * mult_resistencia), 0)
    pre_cena = round(basal + (6.0 * mult_resistencia), 0)
    pico_cena = round(basal + (factor_pico_cena * mult_resistencia), 0)
    nocturna = round(basal + (4.0 * mult_resistencia), 0)

    curva_diaria = [
        {'hora': '07:00 AM', 'momento': 'Ayunas (Basal)', 'glucosa': basal, 'estado': 'normal' if basal < 100 else ('prediabetes' if basal < 126 else 'diabetes')},
        {'hora': '09:00 AM', 'momento': 'Post-Desayuno (+2h)', 'glucosa': pico_desayuno, 'estado': 'normal' if pico_desayuno < 140 else ('prediabetes' if pico_desayuno < 200 else 'diabetes')},
        {'hora': '12:30 PM', 'momento': 'Pre-Almuerzo', 'glucosa': pre_almuerzo, 'estado': 'normal' if pre_almuerzo < 110 else ('prediabetes' if pre_almuerzo < 130 else 'diabetes')},
        {'hora': '02:30 PM', 'momento': 'Post-Almuerzo (+2h)', 'glucosa': pico_almuerzo, 'estado': 'normal' if pico_almuerzo < 140 else ('prediabetes' if pico_almuerzo < 200 else 'diabetes')},
        {'hora': '07:00 PM', 'momento': 'Pre-Cena', 'glucosa': pre_cena, 'estado': 'normal' if pre_cena < 110 else ('prediabetes' if pre_cena < 130 else 'diabetes')},
        {'hora': '09:00 PM', 'momento': 'Post-Cena (+2h)', 'glucosa': pico_cena, 'estado': 'normal' if pico_cena < 140 else ('prediabetes' if pico_cena < 200 else 'diabetes')},
        {'hora': '11:00 PM', 'momento': 'Nocturna (Reposo)', 'glucosa': nocturna, 'estado': 'normal' if nocturna < 115 else ('prediabetes' if nocturna < 135 else 'diabetes')}
    ]

    dias_semana_nombres = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    variaciones_caloricas = [0.95, 0.98, 1.02, 0.97, 1.05, 1.15, 1.08]
    curva_semanal = []
    
    for i, dia_nombre in enumerate(dias_semana_nombres):
        cal_dia = round(calorias_promedio_dia * variaciones_caloricas[i], 0)
        glucosa_media_dia = round((basal * 0.4) + (pico_almuerzo * 0.35) + (pico_cena * 0.25) * (cal_dia / max(1000, calorias_meta_dia)), 0)
        curva_semanal.append({
            'dia': dia_nombre,
            'calorias': cal_dia,
            'glucosa_media': glucosa_media_dia,
            'estado': 'normal' if glucosa_media_dia < 120 else ('prediabetes' if glucosa_media_dia < 160 else 'diabetes')
        })

    if categoria_codigo == 'diabetes':
        motivo = (f"El paciente acumula un Score FINDRISC de alto riesgo ({score} pts), sumado a la presencia de síntomas cardinales de alarma "
                  f"(orina frecuente, sed constante o pérdida ponderal) y una alimentación semanal con sobrecarga glucémica. "
                  f"La curva proyectada del glucómetro supera el límite crítico de ayunas (≥ 126 mg/dL) o postprandial (≥ 200 mg/dL).")
        recs_medicas = [
            "Consultar de forma prioritaria con un médico general o endocrinólogo para realizar una prueba confirmatoria de laboratorio (Glucemia en ayunas y HbA1c).",
            "Iniciar monitoreo glucémico estructurado y vigilancia de síntomas de deshidratación o cetosis.",
            "Evitar suspender tratamientos médicos previos sin la supervisión del facultativo."
        ]
        recs_nutricionales = [
            "Eliminar por completo bebidas azucaradas, jugos industriales, panadería refinada y frituras.",
            "Distribuir las comidas en 4 tomas de menor volumen con alta presencia de vegetales verdes y proteínas magras.",
            "Consumir al menos 2 litros de agua pura al día para asistir la eliminación renal de solutos."
        ]
    elif categoria_codigo in ['prediabetes', 'preliminar']:
        motivo = (f"El paciente presenta un nivel de riesgo intermedio-elevado ({score} pts) según su perfil antropométrico "
                  f"(IMC {imc} kg/m² - {imc_categoria}), antecedentes y consumo calórico semanal. "
                  f"Los valores proyectados se sitúan en rango de alteración de glucosa en ayunas (100-125 mg/dL) o intolerancia a carbohidratos (140-199 mg/dL).")
        recs_medicas = [
            "La prediabetes es 100% reversible con intervención temprana en hábitos de estilo de vida.",
            "Programar una prueba de laboratorio formal (Glucemia en Ayunas y Prueba de Tolerancia PTOG) para ratificación diagnóstica.",
            "Controlar la presión arterial y el perfil lipídico (colesterol y triglicéridos) anualmente."
        ]
        recs_nutricionales = [
            "Reducir en un 40% las porciones de carbohidratos simples (arroz blanco, plátano frito, harinas).",
            "Incorporar fibra soluble diariamente (avena integral, chía, legumbres y verduras al vapor).",
            "Realizar un mínimo de 150 minutos semanales de ejercicio aeróbico y de fuerza muscular."
        ]
    else:
        motivo = (f"El paciente presenta un perfil metabólico favorable ({score} pts en escala FINDRISC). "
                  f"Su IMC ({imc} kg/m²), ausencia de síntomas severos y balance nutricional mantienen las estimaciones glucémicas dentro de rangos normales (< 100 mg/dL en ayunas y < 140 mg/dL tras comidas).")
        recs_medicas = [
            "Mantener chequeos médicos preventivos anuales.",
            "Continuar con hábitos de vida activos y control periódico de peso."
        ]
        recs_nutricionales = [
            "Continuar con una alimentación equilibrada basada en la dieta mediterránea o tradicional variada.",
            "Mantener buena hidratación y moderar el consumo de ultraprocesados en eventos sociales."
        ]

    folio_id = f"ABP-UNISINU-{datetime.datetime.now().strftime('%Y')}-{random.randint(10000, 99999)}"
    fecha_emision = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    return {
        'folio': folio_id,
        'fecha_emision': fecha_emision,
        'nombre': nombre,
        'telefono': telefono,
        'correo': correo,
        'direccion': direccion,
        'edad': edad,
        'peso': peso,
        'estatura': estatura,
        'genero': genero,
        'imc': imc,
        'imc_categoria': imc_categoria,
        'imc_color': imc_color,
        'antecedente_familiar': antecedente_familiar,
        'actividad': actividad,
        'antecedentes_medicos': antecedentes_medicos,
        'transcripcion_audio': transcripcion_audio,
        'sintomas_reportados': sintomas_lista,
        'sintomas_cardinales_detectados': cardinales_presentes,
        'calorias_semana_total': calorias_semana,
        'calorias_promedio_dia': calorias_promedio_dia,
        'calorias_meta_dia': calorias_meta_dia,
        'balance_calorico': balance_calorico,
        'carbohidratos_promedio': carbohidratos_promedio,
        'score_findrisc': score,
        'diagnostico': diagnostico,
        'categoria_codigo': categoria_codigo,
        'nivel_riesgo': nivel_riesgo,
        'color': color,
        'porcentaje_medidor': porcentaje_medidor,
        'glucosa_basal_estimada': basal,
        'glucosa_maxima_postprandial': pico_almuerzo,
        'curva_diaria': curva_diaria,
        'curva_semanal': curva_semanal,
        'factores_detectados': factores_detectados,
        'motivo_clinico': motivo,
        'recomendaciones_medicas': recs_medicas,
        'recomendaciones_nutricionales': recs_nutricionales,
        'es_critico': categoria_codigo in ['diabetes', 'preliminar', 'prediabetes']
    }

# ==============================================================================
# RUTAS DEL SERVIDOR WEB FLASK
# ==============================================================================
@app.route('/')
@app.route('/index.html')
@app.route('/app')
@app.route('/presentacion')
def pagina_principal():
    """
    Página principal interactiva centrada en los 3 círculos del diseño solicitado:
    1. Icono Persona (Perfil, Antecedentes, Grabación de Voz & Integrantes)
    2. Icono Comida (Calendario Semanal de Comidas & Contador de Calorías)
    3. Icono Diagrama (IA Detector de Comidas, Glucometría & Ficha Térmica/PDF)
    """
    return render_template('index.html')

@app.route('/evaluador-laboratorio')
@app.route('/laboratorio')
def evaluador_laboratorio():
    """Formulario complementario con ingreso manual de pruebas de laboratorio."""
    return render_template('index_laboratorio.html')

@app.route('/imagenes/<path:filename>')
def serve_imagenes(filename):
    return send_from_directory('imagenes', filename)

@app.route('/api/ia_detectar_comida', methods=['POST'])
def api_ia_detectar_comida():
    datos = request.get_json() or request.form.to_dict()
    resultado = ia_analizar_alimento(datos)
    return jsonify(resultado)

@app.route('/api/extraer_sintomas_voz', methods=['POST'])
def api_extraer_sintomas_voz():
    datos = request.get_json() or request.form.to_dict()
    texto = datos.get('texto', '')
    sintomas = extraer_sintomas_de_texto(texto)
    return jsonify({'sintomas': sintomas, 'texto': texto})

@app.route('/api/evaluar_predictivo', methods=['POST'])
def api_evaluar_predictivo():
    datos = request.get_json() or request.form.to_dict()
    resultado = evaluar_riesgo_sin_laboratorio(datos)

    correo_destino = datos.get('correo', '').strip()
    if correo_destino and '@' in correo_destino:
        exito, msg_correo = enviar_correo_resultado(correo_destino, resultado['nombre'], resultado)
        resultado['correo_enviado'] = exito
        resultado['correo_mensaje'] = msg_correo
    else:
        resultado['correo_enviado'] = False
        resultado['correo_mensaje'] = 'No se proporcionó correo electrónico para envío automático.'

    return jsonify(resultado)

@app.route('/api/evaluar', methods=['POST'])
def api_evaluar_tradicional():
    datos = request.get_json() or request.form.to_dict()
    resultado = calcular_riesgo_diabetes(datos)
    if 'error' in resultado:
        return jsonify(resultado), 400

    correo_destino = datos.get('correo', '').strip()
    if correo_destino:
        exito, msg_correo = enviar_correo_resultado(correo_destino, resultado['nombre'], resultado)
        resultado['correo_enviado'] = exito
        resultado['correo_mensaje'] = msg_correo
    else:
        resultado['correo_enviado'] = False
        resultado['correo_mensaje'] = 'No se proporcionó correo electrónico.'

    return jsonify(resultado)

if __name__ == '__main__':
    print("Iniciando Servidor Web - Evaluación Clínica de Diabetes Mellitus ABP Universidad del Sinú...")
    app.run(debug=True, port=5000)

