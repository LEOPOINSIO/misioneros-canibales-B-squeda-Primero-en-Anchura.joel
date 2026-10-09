import sys


from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsLineItem
)
from PySide6.QtGui import (
    QColor,
    QBrush,
    QPen,
    QFont,
    QPainter
)
from PySide6.QtCore import Qt, QRectF, QTimer
from dataclasses import dataclass
from collections import deque # FIFO


# REPRESENTACIÓN DEL ESTADO

@dataclass(frozen=True)
class Estado:
    misioneros_izquierda: int
    canibales_izquierda: int
    lado_barca: str

    def __str__(self) -> str:
        return (
            f"({self.misioneros_izquierda}, "
            f"{self.canibales_izquierda}, "
            f"{self.lado_barca})"
        )

@dataclass(frozen=True)
class Accion:
    misioneros: int
    canibales: int
    direccion: str

    def __str__(self) -> str:
        return (
            f"{self.misioneros} M, "
            f"{self.canibales} C "
            f"{self.direccion}"
        )

@dataclass
class NodoBusqueda:
    estado: Estado
    padre: "NodoBusqueda | None" = None
    accion: Accion | None = None
    profundidad: int = 0


@dataclass
class EventoBusqueda:
    tipo: str
    nodo: NodoBusqueda
    accion: Accion | None = None
    estado_resultante: Estado | None = None


# REGLAS DE SEGURIDAD

def es_orilla_segura(misioneros: int, canibales:int) -> bool:
    if misioneros == 0:
        return True

    return misioneros >= canibales

def es_estado_seguro(estado: Estado, total_misioneros: int, total_canibales: int) -> bool:
    
    misioneros_derecha = (total_misioneros - estado.misioneros_izquierda)

    canibales_derecha = (total_canibales - estado.canibales_izquierda)

    izquierda_segura = es_orilla_segura(estado.misioneros_izquierda, estado.canibales_izquierda)

    derecha_segura = es_orilla_segura(misioneros_derecha, canibales_derecha)

    return izquierda_segura and derecha_segura


# FUNCIÓN SUCESORA

def generar_cargas(capacidad: int) -> list[tuple[int, int]]:
    cargas = []

    for misioneros in range(capacidad + 1):
        for canibales in range(capacidad + 1):
            total_personas = misioneros + canibales

            if total_personas < 1 or total_personas > capacidad:
                continue

            if misioneros > 0 and canibales > misioneros:
                continue

            cargas.append((misioneros, canibales))

    return cargas


def generar_sucesores(estado:Estado, total_misioneros: int, total_canibales: int, capacidad: int) -> list[tuple[Accion, Estado]]:
    sucesores = []

    cargas = generar_cargas(capacidad)

    for misioneros_barca, canibales_barca in cargas:
        if estado.lado_barca == "I":
            
            if misioneros_barca > estado.misioneros_izquierda:
                continue

            if canibales_barca > estado.canibales_izquierda:
                continue

            nuevo_estado = Estado(
                estado.misioneros_izquierda - misioneros_barca,
                estado.canibales_izquierda - canibales_barca,
                "D"
            )

            accion = Accion(
                misioneros_barca,
                canibales_barca,
                "→"
            )
        else:

            misioneros_derecha = (total_misioneros - estado.misioneros_izquierda)

            canibales_derecha = (total_canibales - estado.canibales_izquierda)

            if misioneros_barca > misioneros_derecha:
                continue

            if canibales_barca > canibales_derecha:
                continue

            nuevo_estado = Estado(
                estado.misioneros_izquierda + misioneros_barca,
                estado.canibales_izquierda + canibales_barca,
                "I"
            )

            accion = Accion(
                misioneros_barca,
                canibales_barca,
                "←"
            )

        if es_estado_seguro(nuevo_estado, total_misioneros, total_canibales):
            sucesores.append((accion, nuevo_estado))

    return sucesores


# PRUEBA DE META

def es_meta(estado: Estado) -> bool:
    return (
        estado.misioneros_izquierda == 0
        and estado.canibales_izquierda == 0
        and estado.lado_barca == "D"
    )

            
# BÚSQUEDA PRIMERO EN ANCHURA

def busqueda_primero_anchura(estado_inicial: Estado, total_misioneros: int, total_canibales: int,capacidad: int):
    nodo_inicial = NodoBusqueda(
        estado=estado_inicial,
        profundidad=0
    )

    frontera = deque([
        nodo_inicial
    ])

    visitados = {
        estado_inicial
    }

    nodos_generados = [
        nodo_inicial
    ]

    nodos_visualizacion = [
        nodo_inicial
    ]

    eventos = []

    nodos_meta = []

    profundidad_solucion = None

    while frontera:
        nodo_actual = frontera.popleft()

        if (
            profundidad_solucion is not None
            and nodo_actual.profundidad
            >= profundidad_solucion
        ):
            break

        eventos.append(
            EventoBusqueda(
                tipo="EXPANDIR",
                nodo=nodo_actual
            )
        )

        sucesores = generar_sucesores(
            nodo_actual.estado,
            total_misioneros,
            total_canibales,
            capacidad
        )

        for accion, nuevo_estado in sucesores:

            profundidad_hijo = (
                nodo_actual.profundidad + 1
            )

            # META

            if es_meta(nuevo_estado):

                if profundidad_solucion is None:
                    profundidad_solucion = (
                        profundidad_hijo
                    )

                if (
                    profundidad_hijo
                    == profundidad_solucion
                ):
                    nodo_meta = NodoBusqueda(
                        estado=nuevo_estado,
                        padre=nodo_actual,
                        accion=accion,
                        profundidad=profundidad_hijo
                    )

                    nodos_meta.append(
                        nodo_meta
                    )

                    nodos_visualizacion.append(
                        nodo_meta
                    )

                    if nuevo_estado not in visitados:
                        visitados.add(
                            nuevo_estado
                        )

                        nodos_generados.append(
                            nodo_meta
                        )

                    eventos.append(
                        EventoBusqueda(
                            tipo="GENERAR",
                            nodo=nodo_meta,
                            accion=accion,
                            estado_resultante=nuevo_estado
                        )
                    )

                continue

            # ESTADO REPETIDO

            if nuevo_estado in visitados:

                nodo_repetido = NodoBusqueda(
                    estado=nuevo_estado,
                    padre=nodo_actual,
                    accion=accion,
                    profundidad=profundidad_hijo
                )

                nodos_visualizacion.append(
                    nodo_repetido
                )

                eventos.append(
                    EventoBusqueda(
                        tipo="REPETIDO",
                        nodo=nodo_repetido,
                        accion=accion,
                        estado_resultante=nuevo_estado
                    )
                )

                continue

            # NUEVO ESTADO

            visitados.add(
                nuevo_estado
            )

            nodo_hijo = NodoBusqueda(
                estado=nuevo_estado,
                padre=nodo_actual,
                accion=accion,
                profundidad=profundidad_hijo
            )

            nodos_generados.append(
                nodo_hijo
            )

            nodos_visualizacion.append(
                nodo_hijo
            )

            eventos.append(
                EventoBusqueda(
                    tipo="GENERAR",
                    nodo=nodo_hijo,
                    accion=accion,
                    estado_resultante=nuevo_estado
                )
            )

            if profundidad_solucion is None:
                frontera.append(
                    nodo_hijo
                )

    # FIN DE LA BÚSQUEDA

    if nodos_meta:
        eventos.append(
            EventoBusqueda(
                tipo="FINALIZAR",
                nodo=nodos_meta[0]
            )
        )

    return (
        nodos_meta,
        nodos_generados,
        nodos_visualizacion,
        eventos
    )


# RECONSTRUCCIÓN DE LA SOLUCIÓN

def reconstruir_solucion(nodo_meta: NodoBusqueda):
    solucion = []

    nodo_actual = nodo_meta

    while nodo_actual is not None:
        solucion.append(nodo_actual)
        nodo_actual = nodo_actual.padre

    solucion.reverse()

    return solucion


# CÁLCULO DE LA CAPACIDAD DE LA BARCA

def calcular_capacidad(total_misioneros: int, total_canibales: int):
    if total_misioneros == 0 and total_canibales == 0:
        return 0

    if total_misioneros == 0:
        return 2

    if total_canibales > total_misioneros:
        return None

    if total_misioneros > total_canibales:
        return 2

    if total_canibales <= 3:
        return 2

    if total_canibales <= 5:
        return 3

    return 4


# NODO VISUAL DEL ÁRBOL

class NodoVisual(QGraphicsRectItem):
    def __init__(
        self,
        estado: Estado,
        total_misioneros: int,
        total_canibales: int
    ):
        super().__init__(0, 0, 280, 170)

        self.estado = estado
        self.total_misioneros = total_misioneros
        self.total_canibales = total_canibales

        self.misioneros_derecha = (
            total_misioneros
            - estado.misioneros_izquierda
        )

        self.canibales_derecha = (
            total_canibales
            - estado.canibales_izquierda
        )

        self.setBrush(
            QBrush(QColor("#252525"))
        )

        self.setPen(
            QPen(QColor("#9e9e9e"), 2)
        )

    def paint(
        self,
        pintor: QPainter,
        opcion,
        widget=None
    ):
        pintor.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        super().paint(
            pintor,
            opcion,
            widget
        )

        # ESTADO

        fuente_estado = QFont()
        fuente_estado.setPointSize(11)
        fuente_estado.setBold(True)

        pintor.setFont(fuente_estado)
        pintor.setPen(QColor("#ffffff"))

        pintor.drawText(
            QRectF(0, 8, 280, 25),
            Qt.AlignmentFlag.AlignCenter,
            str(self.estado)
        )


        # DIVISIONES

        pintor.setPen(
            QPen(QColor("#555555"), 1)
        )

        pintor.drawLine(
            0,
            38,
            280,
            38
        )

        pintor.fillRect(
            QRectF(110, 39, 60, 130),
            QBrush(QColor("#173447"))
        )

        # TÍTULOS

        fuente_titulo = QFont()
        fuente_titulo.setPointSize(8)
        fuente_titulo.setBold(True)

        pintor.setFont(fuente_titulo)
        pintor.setPen(QColor("#dddddd"))

        pintor.drawText(
            QRectF(5, 43, 100, 20),
            Qt.AlignmentFlag.AlignCenter,
            "IZQUIERDA"
        )

        pintor.drawText(
            QRectF(175, 43, 100, 20),
            Qt.AlignmentFlag.AlignCenter,
            "DERECHA"
        )

        # RÍO

        pintor.setPen(QColor("#64b5f6"))

        pintor.drawText(
            QRectF(110, 73, 60, 50),
            Qt.AlignmentFlag.AlignCenter,
            "≈ ≈ ≈\nRÍO\n≈ ≈ ≈"
        )

        # PERSONAS

        self.dibujar_grupo(
            pintor,
            15,
            70,
            self.estado.misioneros_izquierda,
            "M",
            QColor("#81c784")
        )

        self.dibujar_grupo(
            pintor,
            15,
            105,
            self.estado.canibales_izquierda,
            "C",
            QColor("#ef5350")
        )

        self.dibujar_grupo(
            pintor,
            185,
            70,
            self.misioneros_derecha,
            "M",
            QColor("#81c784")
        )

        self.dibujar_grupo(
            pintor,
            185,
            105,
            self.canibales_derecha,
            "C",
            QColor("#ef5350")
        )

        # BARCA

        pintor.setPen(
            QPen(QColor("#ffd54f"), 2)
        )

        if self.estado.lado_barca == "I":
            posicion_barca_x = 72
        else:
            posicion_barca_x = 178

        pintor.drawLine(
            posicion_barca_x,
            145,
            posicion_barca_x + 30,
            145
        )

        pintor.drawLine(
            posicion_barca_x + 5,
            145,
            posicion_barca_x + 10,
            155
        )

        pintor.drawLine(
            posicion_barca_x + 25,
            145,
            posicion_barca_x + 20,
            155
        )

        pintor.drawLine(
            posicion_barca_x + 10,
            155,
            posicion_barca_x + 20,
            155
        )

        pintor.setFont(
            QFont("", 7)
        )

        pintor.drawText(
            QRectF(
                posicion_barca_x - 5,
                130,
                40,
                15
            ),
            Qt.AlignmentFlag.AlignCenter,
            "BARCA"
        )

    def dibujar_grupo(
        self,
        pintor: QPainter,
        x: int,
        y: int,
        cantidad: int,
        letra: str,
        color: QColor
    ):
        pintor.setFont(
            QFont("", 8, QFont.Weight.Bold)
        )

        pintor.setPen(
            QColor("#ffffff")
        )

        pintor.drawText(
            QRectF(
                x,
                y,
                80,
                25
            ),
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
            f"{letra}: {cantidad}"
        )

        if cantidad == 0:
            return

        cantidad_visible = min(
            cantidad,
            5
        )

        for indice in range(cantidad_visible):
            posicion_x = (
                x
                + 32
                + indice * 13
            )

            pintor.setBrush(
                QBrush(color)
            )

            pintor.setPen(
                QPen(color, 1)
            )

            pintor.drawEllipse(
                posicion_x,
                y + 6,
                8,
                8
            )

        if cantidad > 5:
            pintor.setPen(
                QColor("#ffffff")
            )

            pintor.drawText(
                QRectF(
                    x + 95,
                    y,
                    30,
                    25
                ),
                Qt.AlignmentFlag.AlignCenter,
                "+"
            )

    def marcar_normal(self):
        self.setPen(
            QPen(QColor("#9e9e9e"), 2)
        )

    def marcar_activo(self):
        self.setPen(
            QPen(QColor("#42a5f5"), 4)
        )

    def marcar_meta(self):
        self.setPen(
            QPen(QColor("#66bb6a"), 6)
        )

    def marcar_repetido(self):
        lapiz = QPen(
            QColor("#ff9800"), 3)

        lapiz.setStyle(
            Qt.PenStyle.DashLine
        )

        self.setPen(lapiz)

    def marcar_solucion(self):
        self.setPen(
            QPen(
                QColor("#66bb6a"), 4)
        )


# VISTA DEL ÁRBOL

class VistaArbol(QGraphicsView):
    def __init__(self, escena):
        super().__init__(escena)

        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )

        self.setDragMode(
            QGraphicsView.DragMode.ScrollHandDrag
        )

        self.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

    def wheelEvent(self, evento):
        zoom_actual = self.transform().m11()

        if evento.angleDelta().y() > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15

        nuevo_zoom = (
            zoom_actual * factor
        )

        if nuevo_zoom < 0.20:
            return

        if nuevo_zoom > 3.0:
            return

        self.scale(
            factor,
            factor
        )


# INTERFAZ GRÁFICA

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Misioneros y Caníbales - Primero en Anchura"
        )
        self.resize(1000, 700)

        self.eventos = []
        self.nodos_generados = []
        self.nodos_visualizacion = []
        self.solucion = []
        self.nodos_meta = []

        self.nodos_visuales = {}
        self.posiciones_nodos = {}

        self.conexiones_visuales = {}
        self.textos_acciones = {}

        self.indice_evento = 0

        self.nodo_visual_activo = None

        self.niveles_dibujados = set()

        self.animacion_pausada = False
        self.animacion_finalizada = False

        self.total_misioneros_actual = 0
        self.total_canibales_actual = 0

        self.temporizador = QTimer(self)

        self.temporizador.timeout.connect(
            self.procesar_siguiente_evento
        )

        self.temporizador.setInterval(450)

        contenedor = QWidget()
        self.setCentralWidget(contenedor)

        diseño_principal = QVBoxLayout(contenedor)

        titulo = QLabel("Misioneros y Caníbales")
        titulo.setStyleSheet(
            "font-size: 24px; "
            "font-weight: bold;"
        )

        subtitulo = QLabel(
            "Resolución mediante Búsqueda Primero en Anchura"
        )

        diseño_principal.addWidget(titulo)
        diseño_principal.addWidget(subtitulo)

        grupo_datos = QGroupBox(
            "Configuración del problema"
        )

        diseño_datos = QHBoxLayout(grupo_datos)

        etiqueta_misioneros = QLabel("Misioneros:")

        self.entrada_misioneros = QSpinBox()
        self.entrada_misioneros.setMinimum(0)
        self.entrada_misioneros.setMaximum(20)
        self.entrada_misioneros.setValue(3)

        etiqueta_canibales = QLabel("Caníbales:")

        self.entrada_canibales = QSpinBox()
        self.entrada_canibales.setMinimum(0)
        self.entrada_canibales.setMaximum(20)
        self.entrada_canibales.setValue(3)

        self.boton_resolver = QPushButton("Resolver")
        self.boton_resolver.clicked.connect(
            self.resolver_problema
        )

        diseño_datos.addWidget(etiqueta_misioneros)
        diseño_datos.addWidget(self.entrada_misioneros)

        diseño_datos.addWidget(etiqueta_canibales)
        diseño_datos.addWidget(self.entrada_canibales)

        diseño_datos.addWidget(self.boton_resolver)

        diseño_principal.addWidget(grupo_datos)

        self.etiqueta_capacidad = QLabel(
            "Capacidad de la barca: -"
        )

        self.etiqueta_estado = QLabel(
            "Ingrese los datos y presione Resolver."
        )

        self.etiqueta_estado.setWordWrap(True)

        diseño_principal.addWidget(
            self.etiqueta_capacidad
        )

        diseño_principal.addWidget(
            self.etiqueta_estado
        )

        grupo_arbol = QGroupBox(
            "Árbol de búsqueda"
        )

        diseño_arbol = QVBoxLayout(
            grupo_arbol
        )

        diseño_superior_arbol = QHBoxLayout()

        diseño_superior_arbol.setSpacing(10)

        # LEYENDA

        self.leyenda_colores = QLabel()

        self.leyenda_colores.setText(
            """
            <b>Leyenda:</b>&nbsp;&nbsp;
            <span style="color:#9e9e9e;">■</span> Nodo normal&nbsp;&nbsp;&nbsp;
            <span style="color:#42a5f5;">■</span> Nodo expandiéndose&nbsp;&nbsp;&nbsp;
            <span style="color:#ff9800;">■</span> Repetido descartado&nbsp;&nbsp;&nbsp;
            <span style="color:#66bb6a;">■</span> Meta / solución
            """
        )

        self.leyenda_colores.setStyleSheet(
            """
            QLabel {
                background-color: rgba(25, 25, 25, 220);
                color: white;
                border: 1px solid #777777;
                border-radius: 5px;
                padding: 8px;
            }
            """
        )

        self.leyenda_colores.setWordWrap(
            False
        )

        diseño_superior_arbol.addWidget(
            self.leyenda_colores
        )

        diseño_superior_arbol.addStretch()

        # CONTROLES DE ANIMACIÓN

        self.boton_pausa = QPushButton(
            "Pausar"
        )

        self.boton_siguiente = QPushButton(
            "Siguiente paso"
        )

        self.boton_reiniciar_animacion = QPushButton(
            "Reiniciar animación"
        )

        self.boton_pausa.setEnabled(
            False
        )

        self.boton_siguiente.setEnabled(
            False
        )

        self.boton_reiniciar_animacion.setEnabled(
            False
        )

        self.boton_pausa.clicked.connect(
            self.alternar_pausa
        )

        self.boton_siguiente.clicked.connect(
            self.avanzar_un_paso
        )

        self.boton_reiniciar_animacion.clicked.connect(
            self.reiniciar_animacion
        )

        diseño_superior_arbol.addWidget(
            self.boton_pausa
        )

        diseño_superior_arbol.addWidget(
            self.boton_siguiente
        )

        diseño_superior_arbol.addWidget(
            self.boton_reiniciar_animacion
        )

        diseño_arbol.addLayout(
            diseño_superior_arbol
        )

        # VISTA DEL ÁRBOL

        self.escena_arbol = QGraphicsScene()

        self.vista_arbol = VistaArbol(
            self.escena_arbol
        )

        self.vista_arbol.setAlignment(
            Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignHCenter
        )

        self.vista_arbol.setMinimumHeight(
            500
        )

        diseño_arbol.addWidget(
            self.vista_arbol
        )

        diseño_principal.addWidget(
            grupo_arbol
        )

    def resolver_problema(self):
        self.limpiar_ejecucion_anterior()
        
        total_misioneros = (
            self.entrada_misioneros.value()
        )

        total_canibales = (
            self.entrada_canibales.value()
        )

        if (
            total_misioneros == 0
            and total_canibales == 0
        ):
            self.etiqueta_capacidad.setText(
                "Capacidad de la barca: 0"
            )

            self.etiqueta_estado.setText(
                "No hay personas que transportar."
            )

            return

        capacidad = calcular_capacidad(
            total_misioneros,
            total_canibales
        )

        if capacidad is None:
            self.etiqueta_capacidad.setText(
                "Capacidad de la barca: -"
            )

            self.etiqueta_estado.setText(
                "Problema imposible: hay más caníbales "
                "que misioneros en el estado inicial."
            )

            return

        self.etiqueta_capacidad.setText(
            f"Capacidad de la barca: {capacidad}"
        )

        estado_inicial = Estado(
            total_misioneros,
            total_canibales,
            "I"
        )

        (
            nodos_meta,
            nodos_generados,
            nodos_visualizacion,
            eventos
        ) = busqueda_primero_anchura(
            estado_inicial,
            total_misioneros,
            total_canibales,
            capacidad
        )

        self.nodos_generados = nodos_generados
        self.nodos_visualizacion = nodos_visualizacion
        self.eventos = eventos
        self.nodos_meta = nodos_meta

        if not nodos_meta:
            self.solucion = []
            self.nodos_meta = []

            self.etiqueta_estado.setText(
                "No se encontró una solución."
            )

            return

        self.solucion = reconstruir_solucion(
            nodos_meta[0]
        )

        self.etiqueta_estado.setText(
            "Solución calculada. "
            "Iniciando visualización de la búsqueda..."
        )

        self.total_misioneros_actual = (
            total_misioneros
        )

        self.total_canibales_actual = (
            total_canibales
        )

        self.iniciar_animacion_arbol()

    def calcular_posiciones_arbol(self):
        self.posiciones_nodos = {}

        if not self.nodos_visualizacion:
            return

        ancho_nodo = 280
        alto_nodo = 170

        separacion_horizontal = 60
        separacion_vertical = 110

        margen_horizontal = 180
        margen_superior = 80

        paso_horizontal = (
            ancho_nodo
            + separacion_horizontal
        )

        paso_vertical = (
            alto_nodo
            + separacion_vertical
        )

        self.separacion_vertical_arbol = (
            paso_vertical
        )

        self.margen_superior_arbol = (
            margen_superior
        )

        # ORGANIZAR NODOS POR NIVEL

        niveles = {}

        for nodo in self.nodos_visualizacion:
            if nodo.profundidad not in niveles:
                niveles[nodo.profundidad] = []

            niveles[nodo.profundidad].append(
                nodo
            )

        profundidad_maxima = max(
            niveles.keys()
        )

        # ORGANIZAR HIJOS POR PADRE

        hijos_por_padre = {}

        for nodo in self.nodos_visualizacion:
            hijos_por_padre[id(nodo)] = []

        for nodo in self.nodos_visualizacion:

            if nodo.padre is not None:

                hijos_por_padre[
                    id(nodo.padre)
                ].append(
                    nodo
                )

        # POSICIÓN INICIAL
        
        centros = {}

        for profundidad in range(
            profundidad_maxima + 1
        ):

            nodos = niveles.get(
                profundidad,
                []
            )

            cantidad = len(nodos)

            if cantidad == 0:
                continue

            ancho_nivel = (
                (cantidad - 1)
                * paso_horizontal
            )

            primer_centro = (
                -ancho_nivel / 2
            )

            for indice, nodo in enumerate(nodos):

                centros[id(nodo)] = (
                    primer_centro
                    + indice
                    * paso_horizontal
                )

        for profundidad in range(
            profundidad_maxima - 1,
            -1,
            -1
        ):

            nodos = niveles.get(
                profundidad,
                []
            )

            objetivos = []

            for nodo in nodos:

                hijos = hijos_por_padre.get(
                    id(nodo),
                    []
                )

                if hijos:

                    centros_hijos = [
                        centros[id(hijo)]
                        for hijo in hijos
                    ]

                    objetivo = (
                        centros_hijos[0]
                        + centros_hijos[-1]
                    ) / 2

                else:

                    objetivo = centros[
                        id(nodo)
                    ]

                objetivos.append(
                    objetivo
                )

            if not objetivos:
                continue

            nuevos_centros = []

            # PRIMER RECORRIDO

            for indice, objetivo in enumerate(
                objetivos
            ):

                if indice == 0:
                    nuevo_centro = objetivo

                else:
                    minimo_permitido = (
                        nuevos_centros[-1]
                        + paso_horizontal
                    )

                    nuevo_centro = max(
                        objetivo,
                        minimo_permitido
                    )

                nuevos_centros.append(
                    nuevo_centro
                )

            centro_objetivos = (
                sum(objetivos)
                / len(objetivos)
            )

            centro_resultado = (
                sum(nuevos_centros)
                / len(nuevos_centros)
            )

            correccion = (
                centro_objetivos
                - centro_resultado
            )

            nuevos_centros = [
                centro + correccion
                for centro
                in nuevos_centros
            ]

            for nodo, centro in zip(
                nodos,
                nuevos_centros
            ):
                centros[id(nodo)] = centro

        centro_minimo = min(
            centros.values()
        )

        centro_maximo = max(
            centros.values()
        )

        desplazamiento_x = (
            margen_horizontal
            + ancho_nodo / 2
            - centro_minimo
        )

        for nodo in self.nodos_visualizacion:

            centro_x = (
                centros[id(nodo)]
                + desplazamiento_x
            )

            posicion_x = (
                centro_x
                - ancho_nodo / 2
            )

            posicion_y = (
                margen_superior
                + nodo.profundidad
                * paso_vertical
            )

            self.posiciones_nodos[
                id(nodo)
            ] = (
                posicion_x,
                posicion_y
            )

        # TAMAÑO DE LA ESCENA

        ancho_real = (
            centro_maximo
            - centro_minimo
            + ancho_nodo
        )

        ancho_escena = max(
            1400,
            ancho_real
            + margen_horizontal * 2
        )

        alto_escena = (
            margen_superior
            + (profundidad_maxima + 1)
            * paso_vertical
            + 180
        )

        self.escena_arbol.setSceneRect(
            0,
            0,
            ancho_escena,
            alto_escena
        )

    def dibujar_nodo(self, nodo: NodoBusqueda):
        identificador = id(nodo)

        self.dibujar_nivel_arbol(
            nodo.profundidad
        )

        if identificador in self.nodos_visuales:
            return self.nodos_visuales[
                identificador
            ]

        nodo_visual = NodoVisual(
            nodo.estado,
            self.total_misioneros_actual,
            self.total_canibales_actual
        )

        posicion_x, posicion_y = (
            self.posiciones_nodos[
                identificador
            ]
        )

        nodo_visual.setPos(
            posicion_x,
            posicion_y
        )

        nodo_visual.setZValue(2)

        self.escena_arbol.addItem(
            nodo_visual
        )

        self.nodos_visuales[
            identificador
        ] = nodo_visual

        return nodo_visual

    def dibujar_conexion(
        self,
        nodo_padre: NodoBusqueda,
        nodo_hijo: NodoBusqueda,
        accion: Accion
    ):
        identificador_padre = id(nodo_padre)
        identificador_hijo = id(nodo_hijo)

        nodo_visual_padre = (
            self.nodos_visuales[
                identificador_padre
            ]
        )

        nodo_visual_hijo = (
            self.nodos_visuales[
                identificador_hijo
            ]
        )

        posicion_padre = (
            nodo_visual_padre.scenePos()
        )

        posicion_hijo = (
            nodo_visual_hijo.scenePos()
        )

        x_inicio = posicion_padre.x() + 140
        y_inicio = posicion_padre.y() + 170

        x_fin = posicion_hijo.x() + 140
        y_fin = posicion_hijo.y()

        linea = QGraphicsLineItem(
            x_inicio,
            y_inicio,
            x_fin,
            y_fin
        )

        linea.setPen(
            QPen(
                QColor("#8a8a8a"),
                2
            )
        )

        linea.setZValue(0)

        self.escena_arbol.addItem(
            linea
        )

        self.conexiones_visuales[
            identificador_hijo
        ] = linea

        texto_accion = QGraphicsTextItem(
            str(accion)
        )

        texto_accion.setDefaultTextColor(
            QColor("#dddddd")
        )

        texto_accion.setFont(
            QFont("", 8)
        )

        centro_x = (
            x_inicio + x_fin
        ) / 2

        centro_y = (
            y_inicio + y_fin
        ) / 2

        texto_accion.setPos(
            centro_x - 35,
            centro_y - 12
        )

        texto_accion.setZValue(1)

        self.escena_arbol.addItem(
            texto_accion
        )

        self.textos_acciones[
            identificador_hijo
        ] = texto_accion

    def iniciar_animacion_arbol(self):
        self.temporizador.stop()

        self.animacion_pausada = False
        self.animacion_finalizada = False

        self.boton_pausa.setText(
            "Pausar"
        )

        self.boton_pausa.setEnabled(True)

        self.boton_siguiente.setEnabled(False)

        self.boton_reiniciar_animacion.setEnabled(True)

        self.escena_arbol.clear()

        self.vista_arbol.resetTransform()

        self.nodos_visuales = {}
        self.posiciones_nodos = {}

        self.conexiones_visuales = {}
        self.textos_acciones = {}

        self.indice_evento = 0
        self.nodo_visual_activo = None

        self.calcular_posiciones_arbol()

        self.niveles_dibujados = set()

        nodo_inicial = (
            self.nodos_generados[0]
        )

        nodo_visual_inicial = (
            self.dibujar_nodo(
                nodo_inicial
            )
        )

        nodo_visual_inicial.marcar_activo()

        self.nodo_visual_activo = (
            nodo_visual_inicial
        )

        self.vista_arbol.centerOn(
            nodo_visual_inicial
        )

        self.temporizador.start()

    def procesar_siguiente_evento(self):
        if self.indice_evento >= len(self.eventos):
            self.temporizador.stop()

            self.animacion_finalizada = True

            self.boton_pausa.setEnabled(
                False
            )

            self.boton_siguiente.setEnabled(
                False
            )

            self.boton_reiniciar_animacion.setEnabled(
                True
            )

            return

        evento = self.eventos[
            self.indice_evento
        ]

        self.indice_evento += 1

        if evento.tipo == "EXPANDIR":

            if self.nodo_visual_activo is not None:
                self.nodo_visual_activo.marcar_normal()

            identificador = id(
                evento.nodo
            )

            if identificador in self.nodos_visuales:

                nodo_visual = (
                    self.nodos_visuales[
                        identificador
                    ]
                )

                nodo_visual.marcar_activo()

                self.nodo_visual_activo = (
                    nodo_visual
                )

            self.etiqueta_estado.setText(
                f"Expandiendo estado "
                f"{evento.nodo.estado} "
                f"en profundidad "
                f"{evento.nodo.profundidad}."
            )

        elif evento.tipo == "GENERAR":

            nodo_hijo = evento.nodo

            nodo_padre = nodo_hijo.padre

            self.dibujar_nodo(
                nodo_hijo
            )

            self.dibujar_conexion(
                nodo_padre,
                nodo_hijo,
                evento.accion
            )

            self.etiqueta_estado.setText(
                f"Nuevo estado generado: "
                f"{nodo_hijo.estado}"
            )

        elif evento.tipo == "REPETIDO":

            nodo_repetido = evento.nodo
            nodo_padre = nodo_repetido.padre

            nodo_visual_repetido = (
                self.dibujar_nodo(
                    nodo_repetido
                )
            )

            self.dibujar_conexion(
                nodo_padre,
                nodo_repetido,
                evento.accion
            )

            nodo_visual_repetido.marcar_repetido()

            self.etiqueta_estado.setText(
                f"Estado repetido descartado: "
                f"{evento.estado_resultante}"
            )

        elif evento.tipo == "FINALIZAR":

            self.temporizador.stop()

            self.animacion_finalizada = True
            self.animacion_pausada = False

            self.boton_pausa.setEnabled(
                False
            )

            self.boton_siguiente.setEnabled(
                False
            )

            self.boton_reiniciar_animacion.setEnabled(
                True
            )

            self.boton_pausa.setText(
                "Pausar"
            )

            # Primera solución: ruta completa en verde.
            self.marcar_ruta_solucion()

            # Otras soluciones: nodo meta en verde.
            self.marcar_metas_adicionales()

            cantidad_viajes = (
                len(self.solucion) - 1
            )

            cantidad_soluciones = (
                len(self.nodos_meta)
            )

            self.etiqueta_estado.setText(
                f"¡Búsqueda finalizada! \n"
                f"Soluciones óptimas encontradas: "
                f"{cantidad_soluciones}. \n"
                f"Cantidad de viajes: "
                f"{cantidad_viajes}. \n"
                f"Profundidad: "
                f"{evento.nodo.profundidad}."
            )

    def dibujar_nivel_arbol(self, profundidad: int):

        if profundidad in self.niveles_dibujados:
            return

        self.niveles_dibujados.add(
            profundidad
        )

        ancho_escena = (
            self.escena_arbol.sceneRect().width()
        )

        posicion_y = (
            self.margen_superior_arbol
            + profundidad
            * self.separacion_vertical_arbol
        )

        texto_nivel = QGraphicsTextItem(
            f"Nivel n = {profundidad}"
        )

        texto_nivel.setDefaultTextColor(
            QColor("#bdbdbd")
        )

        texto_nivel.setFont(
            QFont(
                "",
                9,
                QFont.Weight.Bold
            )
        )

        texto_nivel.setPos(
            20,
            posicion_y + 65
        )

        texto_nivel.setZValue(5)

        self.escena_arbol.addItem(
            texto_nivel
        )

        linea_nivel = QGraphicsLineItem(
            120,
            posicion_y + 85,
            ancho_escena - 30,
            posicion_y + 85
        )

        lapiz = QPen(
            QColor("#454545"),
            1
        )

        lapiz.setStyle(
            Qt.PenStyle.DashLine
        )

        linea_nivel.setPen(
            lapiz
        )

        linea_nivel.setZValue(
            -2
        )

        self.escena_arbol.addItem(
            linea_nivel
        )

    def marcar_ruta_solucion(self):
        if not self.solucion:
            return

        for indice, nodo in enumerate(
            self.solucion
        ):
            identificador = id(nodo)

            if identificador in self.nodos_visuales:
                nodo_visual = (
                    self.nodos_visuales[
                        identificador
                    ]
                )

                nodo_visual.marcar_solucion()

            # La raíz no tiene una conexión desde un padre.
            if indice == 0:
                continue

            if identificador in self.conexiones_visuales:
                linea = (
                    self.conexiones_visuales[
                        identificador
                    ]
                )

                linea.setPen(
                    QPen(
                        QColor("#66bb6a"),
                        4
                    )
                )

                linea.setZValue(1)

            if identificador in self.textos_acciones:
                texto_accion = (
                    self.textos_acciones[
                        identificador
                    ]
                )

                texto_accion.setDefaultTextColor(
                    QColor("#81c784")
                )

        nodo_meta = self.solucion[-1]

        identificador_meta = id(
            nodo_meta
        )

        if identificador_meta in self.nodos_visuales:
            self.nodos_visuales[
                identificador_meta
            ].marcar_meta()

    def marcar_metas_adicionales(self):
        if len(self.nodos_meta) <= 1:
            return

        for nodo_meta in self.nodos_meta[1:]:
            identificador = id(
                nodo_meta
            )

            if identificador in self.nodos_visuales:
                self.nodos_visuales[
                    identificador
                ].marcar_meta()

    def alternar_pausa(self):
        if self.animacion_finalizada:
            return

        if self.temporizador.isActive():
            self.temporizador.stop()

            self.animacion_pausada = True

            self.boton_pausa.setText(
                "Reanudar"
            )

            self.boton_siguiente.setEnabled(
                True
            )

            self.etiqueta_estado.setText(
                "Animación pausada."
            )

        else:
            self.animacion_pausada = False

            self.boton_pausa.setText(
                "Pausar"
            )

            self.boton_siguiente.setEnabled(
                False
            )

            self.temporizador.start()

    def avanzar_un_paso(self):
        if self.animacion_finalizada:
            return

        self.temporizador.stop()

        self.animacion_pausada = True

        self.boton_pausa.setText(
            "Reanudar"
        )

        self.boton_siguiente.setEnabled(
            True
        )

        self.procesar_siguiente_evento()

    def reiniciar_animacion(self):
        if not self.eventos:
            return

        self.iniciar_animacion_arbol()

    def limpiar_ejecucion_anterior(self):
        self.temporizador.stop()

        self.eventos = []
        self.nodos_generados = []
        self.nodos_visualizacion = []

        self.solucion = []
        self.nodos_meta = []

        self.nodos_visuales = {}
        self.posiciones_nodos = {}

        self.conexiones_visuales = {}
        self.textos_acciones = {}

        self.niveles_dibujados = set()

        self.indice_evento = 0
        self.nodo_visual_activo = None

        self.animacion_pausada = False
        self.animacion_finalizada = False

        self.escena_arbol.clear()

        self.vista_arbol.resetTransform()

        self.boton_pausa.setText(
            "Pausar"
        )

        self.boton_pausa.setEnabled(
            False
        )

        self.boton_siguiente.setEnabled(
            False
        )

        self.boton_reiniciar_animacion.setEnabled(
            False
        )

# MAIN

def main():
    aplicacion = QApplication(sys.argv)

    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(aplicacion.exec())

if __name__ == "__main__":
    main()