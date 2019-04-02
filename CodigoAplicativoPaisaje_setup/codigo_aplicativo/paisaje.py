'''

Contiene los pasos del procesamiento para la extracción de características del paisaje acústico. Este módulo es invocado
por GUI_paisaje.py

Al usar referenciar:
C. Isaza, D. Duque, S. Buritica and P. Caicedo. “Automatic identification of Landscape Transformation using acoustic recordings classification”, Ecological Informatics, ISSN: 15749541. SUBMITTED 2019
'''


import soundfile as sf
from Indices import *
import pandas as pd

# ----------------------------------------- Funciones de Procesamiento -------------------------------------------------#

def algoritmo_lluvia(avance, param, salida, malas, cod_proc, fin_proc):

    '''

    Esta función filtra las grabaciones con altos niveles de ruido, según la publicación [1]

    Además se genera un umbral automático para el reconocimiento de las grabaciones más ruidosas.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :return: None
    '''

    canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, cod_car = param.get(0)
    param.put((canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, cod_car))
    grabaciones = salida.get(0)
    banda_lluvia = (600, 1200)
    n_grabs = len(grabaciones)
    PSD_medio = np.zeros((n_grabs,))
    grab_malas_df = pd.DataFrame(columns=["Grabaciones rechazadas", "Motivo"])

    for i in range(n_grabs):

        try:
            x, Fs = sf.read(grabaciones[i])
        except RuntimeError:
            grab_malas_df.append({"Grabaciones rechazadas":grabaciones[i].split('\\')[-1], "Motivo":"Archivo corrupto"},
                                 ignore_index=True)
            continue

        if len(x.shape) == 1:
            audio = x
        else:
            audio = x[:, canal]

        puntos_minuto = Fs * 60

        npuntos = len(audio)
        banda = []

        for seg in range(puntos_minuto, npuntos, puntos_minuto):
            f, p = signal.welch(audio[seg - puntos_minuto:seg], Fs, nperseg=tamano_ventana, window=tipo_ventana,
                                nfft=nfft, noverlap=sobreposicion)
            banda.append(p[np.logical_and(f >= banda_lluvia[0], f <= banda_lluvia[1])])

        try:
            banda = np.concatenate(banda)
        except ValueError:
            grab_malas_df.append({"Grabaciones rechazadas":grabaciones[i].split('\\')[-1], "Motivo":"Archivo corrupto"},
                                 ignore_index=True)
            continue

        PSD_medio[i] = np.mean(banda)
        porcentaje = round(100 * (i + 1) / n_grabs, 2)
        print("Corriendo algoritmo de lluvia " + str(porcentaje) + "%")
        avance.put((cod_proc, i + 1))

    PSD_medio = np.array(PSD_medio)
    PSD_medio_sin_ceros = PSD_medio[PSD_medio > 0]
    umbral = (np.mean(PSD_medio_sin_ceros) + stats.mstats.gmean(PSD_medio_sin_ceros)) / 2
    cond_buenas = np.logical_and(PSD_medio < umbral, PSD_medio != 0)
    cond_malas = np.logical_and(PSD_medio >= umbral, PSD_medio != 0)
    grabaciones = np.array(grabaciones)
    grab_buenas = grabaciones[cond_buenas]
    grab_malas = np.array([[grab.split('\\')[-1] for grab in grabaciones[cond_malas]]]).T
    motivos = np.array([["Ruido Fuerte"]*grab_malas.shape[0]]).T
    grab_malas_df=pd.concat([grab_malas_df, pd.DataFrame(np.hstack((grab_malas, motivos)),
                                                         columns=["Grabaciones rechazadas", "Motivo"])],
                            ignore_index=True)

    malas.put(grab_malas_df)
    salida.put(grab_buenas)
    fin_proc.set()
    avance.put((cod_proc, 0))

def calcular_descriptores(avance, param, salida, malas, cod_proc, fin_proc):

    '''

    Este algoritmo calcula los descriptores.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :return: None
    '''

    canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, cod_car = param.get(0)
    param.put((canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, cod_car))
    grab_buenas = salida.get(0)
    valores = []
    nombres_archivo = []
    ngrab_buenas = len(grab_buenas)
    grab_malas_df = malas.get(0)

    for i in range(ngrab_buenas):

        ruta_archivo = grab_buenas[i]
        x, Fs = sf.read(ruta_archivo)

        if len(x.shape) == 2:
            audio = x[:, canal]
        else:
            audio = x

        feats = []
        if indices:

            titulos = ["ACIft", "ADI", "ACItf", "BI", "TE", "ESM", "NDSI", "P", "M", "NP", "MID", "BNF", "BNT", "MD",
                       "FM", "SF", "RMS", "CF", "ADIm1", "ADIm2", "ADIm3", "ADIm4", "ADIm5", "ADIm6", "ADIm7", "ADIm8",
                       "ADIm9", "ADIm10", "ADIm11"]

            nmin = len(audio) // (60 * Fs)
            bio_band = (2000, 8000)
            tech_band = (200, 1500)

            f, t, s = signal.spectrogram(audio, Fs, window=tipo_ventana, nperseg=nmin * tamano_ventana,
                                         mode="magnitude", \
                                         noverlap=sobreposicion, nfft=nmin * nfft)

            ACIf = ACIft(s)

            if np.isnan(ACIf):
                grab_malas_df.append({"Grabaciones rechazadas":grab_buenas[i].split('\\')[-1], "Motivo" : "Archivo discontinuo"},
                                     ignore_index=True)
                continue

            step_av = 1 / 29
            feats.append(ACIf)
            avance.put((cod_proc, i + step_av))
            feats.append(ADI(s, 10000, 1000, -50))
            avance.put((cod_proc, i + 2 * step_av))
            feats.append(ACItf(audio, Fs, 5, s))
            avance.put((cod_proc, i + 3 * step_av))
            feats.append(beta(s, f, bio_band) / nmin)
            avance.put((cod_proc, i + 4 * step_av))
            feats.append(temporal_entropy(audio, Fs))
            avance.put((cod_proc, i + 5 * step_av))
            feats.append(spectral_maxima_entropy(s, f, 482, 8820))
            avance.put((cod_proc, i + 6 * step_av))
            feats.append(NDSI(s, f, bio_band, tech_band))
            avance.put((cod_proc, i + 7 * step_av))
            feats.append(rho(s, f, bio_band, tech_band))
            avance.put((cod_proc, i + 8 * step_av))
            feats.append(median_envelope(audio, Fs, 16))
            avance.put((cod_proc, i + 9 * step_av))
            feats.append(number_of_peaks(s, f, 10 * nmin))
            avance.put((cod_proc, i + 10 * step_av))
            feats.append(mid_band_activity(s, f, 450, 3500))
            avance.put((cod_proc, i + 11 * step_av))
            feats.append(np.mean(background_noise_freq(s)))
            avance.put((cod_proc, i + 12 * step_av))
            feats.append(background_noise_time(wav2SPL(audio, -11, 9, 0.707), 5))
            avance.put((cod_proc, i + 13 * step_av))
            feats.append(musicality_degree(audio, Fs, tamano_ventana, nfft, tipo_ventana, sobreposicion))
            avance.put((cod_proc, i + 14 * step_av))
            feats.append(frequency_modulation(s))
            avance.put((cod_proc, i + 15 * step_av))
            feats.append(wiener_entropy(audio, tamano_ventana, nfft, tipo_ventana, sobreposicion))
            avance.put((cod_proc, i + 16 * step_av))
            feats.append(rms(audio))
            avance.put((cod_proc, i + 17 * step_av))
            feats.append(crest_factor(audio, feats[16]))
            avance.put((cod_proc, i + 18 * step_av))
            feats.extend(list(ADIm(s, Fs, 1000)[:11]))

        else:
            f, mspec = meanspec(audio, Fs, tipo_ventana, sobreposicion, tamano_ventana, nfft)
            feats = list(mspec[np.logical_and(f > fmin, f < fmax)])
            titulos = ["mPSD" + str(feat) for feat in range(len(feats))]

        porcentaje = round(100 * (i + 1) / ngrab_buenas, 2)
        valores.append(feats)
        nombres_archivo.append(ruta_archivo.split('\\')[-1])
        print("Calculando descriptores", str(porcentaje) + "%")  # mensaje en consola
        avance.put((cod_proc, i + 1))

    valores = np.array(valores)
    valores_df = pd.DataFrame(valores, index=nombres_archivo, columns=titulos)
    malas.put(grab_malas_df)
    salida.put(valores_df)
    fin_proc.set()
    avance.put((cod_proc, 0))

def escribir_salida(avance, salida, malas, ruta_salida, cod_proc, fin_proc, leer_excel):

    '''

    Esta función escribe los resultados en dos archivos:

    -Un excel que contiene además de los valores resultantes, una hoja con la lista de las grabaciones "dañadas"
    -Un archivo .dat que es utilizado por SALSA para el reconocimiento automático.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param ruta_salida: recibe un str con la ruta absoluta de salida, en donde serán guardados los archivos resultantes
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :param leer_excel: recibe un Event que indica que el archivo excel de salida está disponible para escribir
    :return: None
    '''

    grab_malas_df = malas.get(0)
    salida = salida.get(0)
    ispsd = len(salida) == 1

    if ispsd:
        valores_df = salida[0]
    else:
        valores_df = salida[1]
        sin_std = salida[0]

    valores_dat_df = valores_df.drop("Codigo", axis=1)
    valores_dat_df = valores_dat_df.dropna(axis=1)
    titulos = list(valores_dat_df)

    ruta_salida_dat = ruta_salida + ".dat"
    ruta_salida_excel = ruta_salida + ".xlsx"

    #Para sobreescribir si el archivo ya existía
    arch_sal = open(ruta_salida_dat, 'w')
    arch_sal.close()

    arch_sal = open(ruta_salida_dat, 'a')
    arch_sal.write("&" + " ".join(titulos) + "\n")
    np.savetxt(arch_sal, valores_dat_df.values, fmt="%1.10f")
    arch_sal.close()

    writer = pd.ExcelWriter(ruta_salida_excel)

    if ispsd:
        valores_df.to_excel(writer, index_label="Dia", sheet_name="descriptores")

    else:
        sin_std.to_excel(writer, index_label="Dia", sheet_name="descriptores")
        valores_df.to_excel(writer, index_label="Dia", sheet_name="estandarizados")

    grab_malas_df.to_excel(writer, sheet_name="rechazadas")

    excel_abierto = True

    while excel_abierto and leer_excel.wait():
        try:
            writer.close()
            excel_abierto = False
        except PermissionError:
            leer_excel.clear()
            fin_proc.set()
            avance.put((-2, None))

    fin_proc.set()
    avance.put((cod_proc, 0))

def estandarizar(recalcular, avance, salida, cod_proc, fin_proc):

    '''

    Esta función estandariza los valores resultantes para el caso de los índices.

    :param recalcular: recibe un bool que indica si se recalculan los parámetros para la estandarización (True) o no (False)
    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param salida: recibe un Queue que guarda la salida del proceso
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :return: None
    '''

    valores_df = salida.get(0)
    valores_df = valores_df[0]
    valores_df_nocod = valores_df.drop("Codigo", axis=1)
    valores = valores_df_nocod.values

    if recalcular:
        mean_data = np.mean(valores, axis=0)
        std_data = np.std(valores, axis=0)
    else:
        '''
        orden = ["ACIft", "ADI", "ACItf", "BI", "TE", "ESM", "NDSI", "P", "M", "NP", "MID", "BNF", "BNT", "MD", "FM", 
        "SF", "RMS", "CF", "ADIm1", "ADIm2", "ADIm3", "ADIm4", "ADIm5", "ADIm6", "ADIm7", "ADIm8", "ADIm9", "ADIm10", 
        "ADIm11"]
        '''

        mean_data = np.array([1826097.11, 1.767735804, 91882.55071, 9905.628921, 0.995067959, 0.957362804, 0.547765376,
                              84.90893082, 734.1874178, 8.572168173, 0.033159709, 0.00000999101, -100.3515103,
                              -9.484889431, 39.81445113, 0.17353751, 87.64207067, 0.001238626, 0.274977545, 0.262761599,
                              0.244770488, 0.234876761, 0.231588818, 0.228887922, 0.224286545, 0.223498633, 0.238339141,
                              0.247948675, 0.25437372])

        std_data = np.array([3776.292478, 0.419878325, 1882.807154, 2182.8824, 0.005377528, 0.015149102, 0.235213006,
                             87.12348419, 331.4517679, 3.987796787, 0.023563694, 0.0000013147, 0.000000000000697625,
                             2.517967474, 0.145361401, 0.102640259, 41.69620717, 0.00209809, 0.015519584,
                             0.020473526, 0.022824243, 0.023105743, 0.022028239, 0.025576337, 0.024031996, 0.026575113,
                             0.028468976, 0.028189446, 0.028091119])

    std_valores = (valores - mean_data) / (std_data)
    titulos_desc = list(valores_df_nocod)
    std_df = pd.DataFrame(std_valores, index=valores_df.index.values, columns=titulos_desc)
    std_df["Codigo"] = valores_df["Codigo"]
    std_df = std_df[["Codigo"] + titulos_desc]
    salida.put((valores_df, std_df))
    fin_proc.set()
    avance.put((cod_proc, None))

def promedios_diarios(avance, param, salida, malas, cod_proc, fin_proc):

    '''

    Calcula los promedios diarios de los descriptores

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :return: None
    '''

    canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, cod_car = param.get(0)
    param.put((canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, cod_car))
    valores_df = salida.get(0)
    grab_malas_df = malas.get(0)
    nombres_archivo = valores_df.index.values
    valores = valores_df.values

    dias = []
    min_grab = (grabxdia * 5) // 6
    cdias = []
    codigos = []
    nfeats = valores.shape[1]
    prom_dia = np.empty((0, nfeats))

    for nombre in nombres_archivo:
        div_nombre = nombre.split('_')
        dia_str = div_nombre[-2]
        if dia_str not in dias:
            dias.append(dia_str)

    ndias = len(dias)

    for d in range(ndias):
        ind_dia = [i for i, nombre_archivo in enumerate(nombres_archivo) if nombre_archivo.split('_')[-2] == dias[d]]
        ndia = len(ind_dia)

        if ndia < min_grab:
            motivos = np.array([ndia*["No alcanza el mínimo diario"]]).T
            grab_malas = np.array([nombres_archivo[ind_dia]]).T
            grab_malas_df = pd.concat([grab_malas_df, pd.DataFrame(np.hstack((grab_malas, motivos)),
                                                                   columns=["Grabaciones rechazadas", "Motivo"])],
                                      ignore_index=True)
            continue

        codigos.append(nombres_archivo[ind_dia[0]].split('_')[0]) #Ojo, se asume que todos los archivos de la carpeta tienen el mismo código
        cdias.append(dias[d])
        datos_dia = valores[ind_dia, :]
        prom_dia = np.append(prom_dia, np.array([np.mean(datos_dia, axis=0)]), axis=0)
        porcentaje = round(100 * (d + 1) / ndias, 2)
        print("Calculando promedios diarios", str(porcentaje) + "%")

    titulos_desc = list(valores_df)
    prom_df = pd.DataFrame(prom_dia, index=cdias, columns=titulos_desc)
    prom_df["Codigo"] = codigos
    prom_df = prom_df[["Codigo"] + titulos_desc]
    malas.put(grab_malas_df)
    salida.put((prom_df,))
    fin_proc.set()
    avance.put((cod_proc, 0))


# --------------------------------------- Fin Funciones de Procesamiento -----------------------------------------------#

'''
Referencias:

[1] Bedoya, C., Isaza, C., Daza, J. M., & López, J. D. (2017). Automatic identification of rainfall in acoustic
    recordings. Ecological Indicators, 75, 95–100. http://doi.org/10.1016/j.ecolind.2016.12.018

'''
