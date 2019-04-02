'''
Interfaz Gráfica y funciones para la extracción de descriptores de paisaje acústico.
al usar referenciar como:
C. Isaza, D. Duque, S. Buritica and P. Caicedo. “Automatic identification of Landscape Transformation using acoustic recordings classification”, Ecological Informatics, ISSN: 15749541. SUBMITTED 2019.
'''

from tkinter import *
from tkinter.filedialog import askdirectory
from tkinter.ttk import Progressbar
from tkinter import messagebox
from multiprocessing import Process, Queue, Event, freeze_support
from queue import Empty
import os
import glob
from paisaje import *

salida = Queue()
param = Queue()
avance = Queue()
malas = Queue()
fin_proc = Event()
leer_excel = Event()
leer_excel.set()
procesos = []
mensajes = []

#---------------------------------------Funciones de la Interfaz Gráfica-----------------------------------------------#

def admin_procesos(avance, param, salida, malas, procesos, mensajes, fin_proc, leer_excel):
    '''

    Esta función ejecuta secuencialmente los algoritmos de procesamiento y se encarga de que puedan comunicarse entre
    ellos

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param procesos: recibe una lista con los procesos que van a ejecutarse (los algoritmos)
    :param mensajes: recibe una lista con cadenas de caracteres que describen cada paso del procesamiento
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :param leer_excel: recibe un Event que indica que el archivo excel de salida está disponible para escribir
    :return: retorna None
    '''

    if fin_proc.is_set():

        p_actual, valor = avance.get()

        if p_actual == -2:
            mensaje_error("Cierre el archivo excel para continuar")
            fin_proc.clear()
            leer_excel.set()

        if p_actual == -1:
            prog_cont["text"] = "Progreso"
            prog_bar.stop()
            procesos.clear()
            mensajes.clear()
            fin_proc.clear()
            cor_bot["state"] = "normal"
            return

        p_actual += 1

        if p_actual == 1:
            global carpetas
            carpetas = salida.get(0)

            msj_ad = " 1/1"
            if len(carpetas) > 1:
                msj_ad = " 1/" + str(len(carpetas))

            canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension = param.get(
                0)
            param.put(
                (canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, 0))
            grabaciones = glob.glob(carpetas[0] + '/*' + extension)
            salida.put(grabaciones)
            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["mode"] = "determinate"
            prog_bar["value"] = 0
            prog_bar["maximum"] = len(grabaciones)
            prog_cont["text"] = mensajes[p_actual] + msj_ad

        elif p_actual == 2:
            canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, \
            cod_car = param.get(0)
            param.put((canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia,
                       extension, cod_car))

            msj_ad = " " + str(cod_car + 1) + "/" + str(len(carpetas))

            sal = salida.get()
            salida.put(sal)
            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["mode"] = "determinate"
            prog_bar["value"] = 0
            prog_bar["maximum"] = len(sal)
            prog_cont["text"] = mensajes[p_actual] + msj_ad

        elif p_actual == 3:
            canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, cod_car = param.get(
                0)
            param.put((canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia,
                       extension, cod_car))

            msj_ad = " " + str(cod_car + 1) + "/" + str(len(carpetas))

            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["value"] = 0
            prog_bar["maximum"] = 100
            prog_bar["mode"] = "indeterminate"
            prog_cont["text"] = mensajes[p_actual] + msj_ad
            prog_bar.start()

        elif p_actual == 4:
            canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension, c_actual = param.get(
                0)

            sal = salida.get(0)
            grab_malas = malas.get(0)

            if "df" not in globals():
                global df
                df = sal[0]

            else:
                df = pd.concat([df, sal[0]])

            sal = (df, )

            if "gm_df" not in globals():
                global gm_df
                gm_df = grab_malas
            else:
                gm_df = pd.concat([gm_df, grab_malas], ignore_index=True)

            if c_actual < len(carpetas) - 1:
                msj_ad = " " + str(c_actual + 2) + "/" + str(len(carpetas))
                p_actual = 1
                param.put((canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia,
                           extension, c_actual + 1))
                grabaciones = glob.glob(carpetas[c_actual + 1] + '/*' + extension)
                salida.put(grabaciones)
                procesos[p_actual] = Process(target=algoritmo_lluvia,
                                             args=(avance, param, salida, malas, p_actual, fin_proc))
                procesos[p_actual + 1] = Process(target=calcular_descriptores,
                                                 args=(avance, param, salida, malas, p_actual + 1, fin_proc))
                procesos[p_actual + 2] = Process(target=promedios_diarios,
                                                 args=(avance, param, salida, malas, p_actual + 2, fin_proc))
                procesos[p_actual].start()
                fin_proc.clear()
                prog_bar.stop()
                prog_bar["mode"] = "determinate"
                prog_bar["value"] = 0
                prog_bar["maximum"] = len(grabaciones)
                prog_cont["text"] = mensajes[p_actual] + msj_ad

            else:
                malas.put(gm_df)
                salida.put(sal)
                procesos[p_actual].start()
                fin_proc.clear()
                prog_bar.stop()
                prog_bar["value"] = 0
                prog_bar["maximum"] = 100
                prog_bar["mode"] = "indeterminate"
                prog_cont["text"] = mensajes[p_actual]
                prog_bar.start()

        elif p_actual in range(5, len(procesos)):
            procesos[p_actual].start()
            fin_proc.clear()
            prog_bar.stop()
            prog_bar["value"] = 0
            prog_bar["maximum"] = 100
            prog_bar["mode"] = "indeterminate"
            prog_cont["text"] = mensajes[p_actual]
            prog_bar.start()

        else:
            prog_bar.stop()
            prog_cont["text"] = "Progreso"
            cor_bot["state"] = "normal"
            mensaje_error("Descriptores guardados correctamente")
            procesos.clear()
            mensajes.clear()
            del df, gm_df
            fin_proc.clear()
            return

    else:

        try:
            p_actual, valor = avance.get(0)
            prog_bar["value"] = valor

        except Empty:
            pass

    ven_pri.after(100, lambda: admin_procesos(avance, param, salida, malas, procesos, mensajes, fin_proc, leer_excel))

def cambio_descriptor(*args):
    '''

    Esta función activa los controles correspondientes al tipo de descriptor seleccionado y desactiva los controles
    del otro tipo de descriptor

    :param args: Recibe unos argumentos por defecto de la interfaz
    :return: retorna None
    '''

    if ftip_var.get() == "PSD":
        std_check['state'] = "disabled"
        win_entry['state'] = "normal"
        fmin_entry['state'] = "normal"
        fmax_entry['state'] = 'normal'

    else:
        std_check['state'] = "normal"
        win_entry['state'] = "disabled"
        fmin_entry['state'] = "disabled"
        fmax_entry['state'] = 'disabled'

def ejecutar_programa(avance, param, salida, malas, fin_proc, read_excel, procesos, mensajes):

    '''

    Esta función se ejecuta cuando se inicia el procesamiento. Crea los procesos y llama admin_procesos para que regule
    el funcionamiento de los algoritmos.

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param malas: recibe un Queue que guarda las grabaciones rechazadas durante el procesamiento
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :param leer_excel: recibe un Event que indica que el archivo excel de salida está disponible para escribir
    :param procesos: recibe una lista con los procesos que van a ejecutarse (los algoritmos)
    :param mensajes: recibe una lista con cadenas de caracteres que describen cada paso del procesamiento
    :return: None
    '''

    cor_bot["state"] = "disabled"
    carpeta_grabaciones = ruta_entry.get()
    extension = '.' + ext_var.get().lower()
    canal_str = can_entry.get()

    if ftip_var.get() == "Índices":
        indices = True
    else:
        indices = False

    fmin_str = fmin_entry.get()
    fmax_str = fmax_entry.get()
    tamano_ventana_str = win_entry.get()
    rec_std = bool(std_var.get())
    grabxdia_str = ngrab_entry.get()
    carpeta_salida = sal_entry.get()
    nombre_salida = nom_entry.get()
    subcarpetas = bool(sub_var.get())

    ruta_salida = carpeta_salida + '/' + nombre_salida

    param.put((subcarpetas, carpeta_grabaciones, extension, canal_str, indices, fmin_str, fmax_str, tamano_ventana_str,
               carpeta_salida, grabxdia_str))

    nproc = 0

    val_proc = Process(target=validar_entradas, args=(avance, param, salida, nproc, fin_proc))
    val_proc.start()
    procesos.append(val_proc)
    prog_cont["text"] = "Verificando entradas"
    mensajes.append("Verificando entradas")
    prog_bar.start()
    nproc += 1

    lluvia_proc = Process(target=algoritmo_lluvia, args=(avance, param, salida, malas, nproc, fin_proc))
    procesos.append(lluvia_proc)
    mensajes.append("Corriendo algoritmo de lluvia...")
    nproc += 1

    desc_proc = Process(target=calcular_descriptores, args=(avance, param, salida, malas, nproc, fin_proc))
    procesos.append(desc_proc)
    mensajes.append("Calculando descriptores...")
    nproc += 1

    prom_proc = Process(target=promedios_diarios, args=(avance, param, salida, malas, nproc, fin_proc))
    procesos.append(prom_proc)
    mensajes.append("Calculando promedios diarios...")
    nproc += 1

    if indices:
        rec_proc = Process(target=estandarizar, args=(rec_std, avance, salida, nproc, fin_proc))
        procesos.append(rec_proc)
        mensajes.append("Estandarizando...")
        nproc += 1

    esc_proc = Process(target=escribir_salida, args=(avance, salida, malas, ruta_salida, nproc, fin_proc, read_excel))
    procesos.append(esc_proc)
    mensajes.append("Escribiendo archivos de salida...")

    admin_procesos(avance, param, salida, malas, procesos, mensajes, fin_proc, read_excel)

def escoger_carpeta(boton):

    '''

    Esta función es invocada cuando se quiere seleccionar una carpeta

    :param boton: Indica el botón que llamó la función (puede ser el botón de la carpeta de entrada o la carpeta de salida
    :return: None
    '''

    ruta = askdirectory()

    if boton == buscar_bot:
        ruta_entry.delete(0, END)
        ruta_entry.insert(0, ruta)

    elif boton == buscars_bot:
        sal_entry.delete(0, END)
        sal_entry.insert(0, ruta)

def mensaje_error(mensaje):

    '''
    Esta función es invocada cuando se presenta un error en el programa. Muestra una ventana con el mensaje de error

    :param mensaje: Str con el mensaje de error a mostrar
    :return: None
    '''

    error_ven = Tk()
    error_ven.withdraw()
    messagebox.showinfo("Aviso", mensaje)
    error_ven.destroy()

def salir(procesos):

    '''

    Esta función es invocada cuando el programa es cerrado por el usuario.

    :param procesos: recibe una lista con los procesos
    :return: None
    '''

    for process in procesos:
        if process.is_alive():
            process.terminate()
    ven_pri.destroy()

def validar_entradas(avance, param, salida, cod_proc, fin_proc):

    '''
    Esta función verifica que los valores ingresados en la interfaz sean correctos

    :param avance: recibe un Queue para indicar a la barra de progreso el avance del procedimiento
    :param param: recibe un Queue con parámetros necesarios para el siguiente proceso
    :param salida: recibe un Queue que guarda la salida del proceso
    :param cod_proc: recibe un entero con el código del proceso
    :param fin_proc: recibe un Event que indica si el proceso actual terminó
    :return: retorna None
    '''

    subcarpetas, carpeta_grabaciones, extension, canal_str, indices, fmin_str, fmax_str, tamano_ventana_str, \
    carpeta_salida, grabxdia_str = param.get(0)

    if not subcarpetas:

        grabaciones = glob.glob(carpeta_grabaciones + '/*' + extension)

        if len(grabaciones) == 0:
            mensaje_error("No se encontraron grabaciones")
            fin_proc.set()
            avance.put((-1, None))
            return

        carpetas = [carpeta_grabaciones]

    else:

        carpetas = []

        for root, dirs, files in os.walk(carpeta_grabaciones):
            for file in files:
                if extension in file:
                    carpetas.append(root)
                    break

    if len(carpetas) == 0:
        mensaje_error("No se encontraron grabaciones")
        fin_proc.set()
        avance.put((-1, None))
        return

    grabaciones = glob.glob(carpetas[0] + '/*' + extension)


    for grab in grabaciones:
        try:
            x, Fs = sf.read(grab)
            break
        except:
            pass

    if not (canal_str+grabxdia_str+fmin_str+fmax_str+tamano_ventana_str).isnumeric():
        mensaje_error("Ingrese valores numéricos")
        fin_proc.set()
        avance.put((-1, None))
        return

    canal = int(canal_str) - 1

    if len(x.shape) <= canal:
        mensaje_error("No existe el canal " + str(canal + 1))
        fin_proc.set()
        avance.put((-1, None))
        return

    tipo_ventana = "hann"
    sobreposicion = 0
    tamano_ventana = int(tamano_ventana_str)
    fmin = int(fmin_str)
    fmax = int(fmax_str)

    if indices:
        tamano_ventana = 1024

    else:
        if tamano_ventana > Fs // 2:
            mensaje_error("Ventana demasiado grande")
            fin_proc.set()
            avance.put((-1, None))
            return

    nfft = tamano_ventana

    if not os.path.isdir(carpeta_salida):
        mensaje_error("Ingrese un directorio de salida válido")
        fin_proc.set()
        avance.put((-1, None))

        return

    grabxdia = int(grabxdia_str)

    salida.put(carpetas)
    param.put((canal, indices, tipo_ventana, tamano_ventana, sobreposicion, nfft, fmin, fmax, grabxdia, extension))
    fin_proc.set()
    avance.put((cod_proc, None))

#------------------------------------- Fin Funciones de la Interfaz Gráfica -------------------------------------------#

# --------------------------------------------- Interfaz Gráfica ------------------------------------------------------#

if __name__ == '__main__': #Se utiliza este if para poder usar varios procesos. (Son necesarios varios procesos para actualizar la barra de progreso)

    freeze_support() #Para correr el programa sin problemas como ejecutable

    ANCHO = 500
    ALTO = 450
    PAD = 7

    # Ventana principal
    ven_pri = Tk()
    ven_pri.geometry(str(ANCHO) + 'x' + str(ALTO))
    ven_pri.title("Descriptores del Paisaje Acústico")
    ven_pri.resizable(width=False, height=False)

    # Frame para selección de carpeta
    carp_cont = LabelFrame(ven_pri, text=" Carpeta con Grabaciones ")
    carp_cont.pack(fill=X, padx=PAD, pady=PAD)
    ruta_entry = Entry(carp_cont, width=45)
    ruta_entry.pack(side=LEFT)
    sub_var = IntVar()
    sub_check = Checkbutton(carp_cont, text="Contiene subcarpetas", justify=CENTER, variable=sub_var, state="normal")
    sub_check.pack(side=LEFT)
    buscar_bot = Button(carp_cont, text="Buscar...", command=lambda: escoger_carpeta(buscar_bot))
    buscar_bot.pack(expand=True)

    # Frame para configuración de grabaciones
    par_cont = LabelFrame(ven_pri, text=" Parámetros ")
    par_cont.pack(fill=X, padx=PAD, pady=PAD)
    can_lab = Label(par_cont, text="Canal:", width=5)
    can_lab.pack(side=LEFT)
    can_entry = Entry(par_cont, width=3, justify=CENTER)
    can_entry.insert(END, "1")
    can_entry.pack(side=LEFT)
    ext_lab = Label(par_cont, text="Formato:", width=8)
    ext_lab.pack(side=LEFT)
    ext_var = StringVar(ven_pri)
    ext_var.set("WAV")
    ext_menu = OptionMenu(par_cont, ext_var, "WAV", "8SVX", "AIFF", "AU", "FLAC", "IFF", "MOGG", "OGA", "OGG", "RAW")
    ext_menu.pack(side=LEFT)
    ftip_lab = Label(par_cont, text="Descriptores:", width=10)
    ftip_lab.pack(side=LEFT)
    ftip_var = StringVar(ven_pri)
    ftip_var.set("Índices")
    ftip_var.trace('w', cambio_descriptor)
    ext_menu = OptionMenu(par_cont, ftip_var, "Índices", "PSD")
    ext_menu.pack(side=LEFT)
    ngrab_lab = Label(par_cont, text="Grabaciones\n diarias:", width=10)
    ngrab_lab.pack(side=LEFT)
    ngrab_entry = Entry(par_cont, width=5, justify=CENTER)
    ngrab_entry.insert(0, "144")
    ngrab_entry.pack(side=LEFT)

    # Frame Configuración que contiene otros frames
    conf_cont = LabelFrame(ven_pri, text=" Configuración de Descriptores ")
    conf_cont.pack(fill=X, padx=PAD, pady=PAD)

    # Frame para configuración de índices
    ind_cont = LabelFrame(conf_cont, text=" Índices ")
    ind_cont.pack(padx=PAD, pady=PAD, side=LEFT)
    std_var = IntVar()
    std_check = Checkbutton(ind_cont, text="Recalcular parámetros para\n estandarización", justify=LEFT, \
                                 variable=std_var, state="normal")
    std_check.pack()

    # Frame para configuración de PSD
    psd_cont = LabelFrame(conf_cont, text=" PSD ")
    psd_cont.pack(anchor=N, pady=PAD)
    win_lab = Label(psd_cont, text="Tamaño ventana:")
    win_lab.pack(side=LEFT)
    win_entry = Entry(psd_cont, width=5, justify=CENTER)
    win_entry.insert(0, "512")
    win_entry.pack(side=LEFT)
    filt_cont = LabelFrame(psd_cont, text=" Aplicar filtro (Hz) ")
    filt_cont.pack(side=LEFT, padx=PAD, pady=PAD)
    fmin_lab = Label(filt_cont, text="Fmin:")
    fmin_lab.grid()
    fmin_entry = Entry(filt_cont, width=10, justify=CENTER)
    fmin_entry.insert(0, "1000")
    fmin_entry.grid(row=0, column=1)
    fmax_lab = Label(filt_cont, text="Fmax:")
    fmax_lab.grid(row=1, column=0)
    fmax_entry = Entry(filt_cont, width=10, justify=CENTER)
    fmax_entry.insert(0, "11250")
    fmax_entry.grid(row=1, column=1)

    cambio_descriptor()

    # Frame para carpeta de salida
    scarp_cont = LabelFrame(ven_pri, text=" Carpeta de Salida ")
    scarp_cont.pack(fill=X, side=TOP, padx=PAD, pady=PAD)
    sal_entry = Entry(scarp_cont, width=65)
    sal_entry.pack(side=LEFT)
    buscars_bot = Button(scarp_cont, text="Buscar...", command=lambda: escoger_carpeta(buscars_bot))
    buscars_bot.pack(expand=True)

    # Parámetros de Salida
    sal_cont = LabelFrame(ven_pri)
    sal_cont.pack(fill=X, padx=PAD, pady=PAD)
    nom_lab = Label(sal_cont, text="Nombre de las Salidas:")
    nom_lab.pack(side=LEFT)
    nom_entry = Entry(sal_cont, justify=CENTER)
    nom_entry.insert(0, "Salida")
    nom_entry.pack(side=LEFT)
    cor_bot = Button(sal_cont, text="Iniciar", width=30,
                     command= lambda : ejecutar_programa(avance, param, salida, malas, fin_proc, leer_excel, procesos, mensajes))
    cor_bot.pack(expand=True)

    # Label de Progreso
    prog_cont = LabelFrame(ven_pri, text="Progreso")
    prog_cont.pack(fill=X, padx=PAD, pady=PAD, ipady=PAD)
    prog_bar = Progressbar(prog_cont, orient="horizontal", mode="indeterminate")
    prog_bar.pack(fill=X, padx=PAD)
    ven_pri.protocol("WM_DELETE_WINDOW", lambda : salir(procesos))
    ven_pri.mainloop()

#--------------------------------------------- Fin Interfaz Gráfica ---------------------------------------------------#
