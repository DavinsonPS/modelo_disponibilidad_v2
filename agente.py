"""
Agente de Disponibilidad de Servicios con LangGraph
Consulta servicios, promesas y afectaciones en SQL Server
"""
import os
from typing import TypedDict, Annotated, Sequence
from operator import add
import tools as ts
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ==================== ESTADO DEL GRAFO ====================

class AgentState(TypedDict):
    # Usar add para concatenar mensajes en lugar de reemplazarlos
    messages: Annotated[Sequence[BaseMessage], add]


# ==================== CONFIGURACIÓN DEL LLM ====================

model_name = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')

llm = ChatOpenAI(
    model=model_name,
    api_key=os.getenv('OPENAI_API_KEY'),
    temperature=0
)

tools = [
    ts.consultar_servicios,
    ts.consultar_promesa_servicio,
    ts.consultar_afectaciones,
    ts.calcular_disponibilidad
]

llm_with_tools = llm.bind_tools(tools)


# ==================== NODOS DEL GRAFO ====================

def llamar_modelo(state: AgentState):
    """Nodo que llama al LLM con las herramientas disponibles"""
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def decidir_continuar(state: AgentState):
    """Decide si continuar ejecutando herramientas o terminar"""
    messages = state['messages']
    last_message = messages[-1]
    
    # Si el último mensaje tiene tool_calls, continuar a las herramientas
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    # Si no, terminar
    return "end"


# ==================== CONSTRUCCIÓN DEL GRAFO ====================

workflow = StateGraph(AgentState)

# Agregar nodos
workflow.add_node("agent", llamar_modelo)
workflow.add_node("tools", ToolNode(tools))

# Configurar punto de entrada
workflow.set_entry_point("agent")

# Agregar edges condicionales
workflow.add_conditional_edges(
    "agent",
    decidir_continuar,
    {
        "tools": "tools",
        "end": END
    }
)

# Después de usar herramientas, volver al agente
workflow.add_edge("tools", "agent")

# Compilar el grafo
app = workflow.compile()


# ==================== FUNCIÓN PRINCIPAL ====================

def consultar_agente(pregunta: str, verbose: bool = False) -> str:
    """
    Procesa una pregunta sobre disponibilidad de servicios.
    
    Args:
        pregunta: Pregunta del usuario
        verbose: Si es True, muestra el proceso paso a paso
    
    Returns:
        Respuesta del agente
    """
    inputs = {"messages": [HumanMessage(content=pregunta)]}
    
    resultado = ""
    step_count = 0
    
    try:
        for output in app.stream(inputs):
            step_count += 1
            
            if verbose:
                print(f"\n{'='*60}")
                print(f"Paso {step_count}: {list(output.keys())}")
                print(f"{'='*60}")
            
            for key, value in output.items():
                if key == "agent":
                    last_msg = value['messages'][-1]
                    if verbose:
                        print(f"🤖 Tipo de mensaje: {type(last_msg).__name__}")
                        if hasattr(last_msg, 'tool_calls'):
                            print(f"   Tool calls: {len(last_msg.tool_calls) if last_msg.tool_calls else 0}")
                    
                    # Solo capturar el contenido si es un mensaje de texto (no tool calls)
                    if hasattr(last_msg, 'content') and last_msg.content and isinstance(last_msg.content, str):
                        resultado = last_msg.content
                        if verbose:
                            print(f"   Contenido: {resultado[:100]}...")
                            
                elif key == "tools":
                    if verbose:
                        print(f"🔧 Ejecutando {len(value['messages'])} herramienta(s)...")
                        for msg in value['messages']:
                            if isinstance(msg, ToolMessage):
                                print(f"   - Herramienta ejecutada: {msg.name if hasattr(msg, 'name') else 'N/A'}")
        
        if not resultado:
            resultado = "No pude procesar tu consulta. Por favor, intenta reformularla."
        
        return resultado
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Error completo: {error_msg}")
        
        if "tool" in error_msg.lower() and "role" in error_msg.lower():
            return (
                "❌ Error: Problema con el manejo de herramientas. "
                f"Detalles técnicos: {error_msg}"
            )
        return f"❌ Error al procesar la consulta: {error_msg}"


# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    print("🤖 Agente de Disponibilidad de Servicios")
    print("=" * 60)
    print(f"Modelo: {os.getenv('OPENAI_MODEL', 'gpt-4-turbo')}")
    print("=" * 60)
    
    # Prueba simple primero
    print("\n🧪 Ejecutando prueba simple...")
    pregunta_prueba = "¿Qué servicios tenemos disponibles?"
    print(f"\n👤 Usuario: {pregunta_prueba}")
    
    try:
        # Ejecutar en modo verbose para ver qué está pasando
        respuesta = consultar_agente(pregunta_prueba, verbose=True)
        print(f"\n✅ Respuesta final:")
        print(f"🤖 Agente: {respuesta}")
    except Exception as e:
        print(f"\n❌ Error en prueba: {str(e)}")
    
    print("\n" + "=" * 60)
    
    # Si la prueba simple funciona, ejecutar ejemplos completos
    continuar = input("\n¿Ejecutar ejemplos completos? (s/n): ")
    
    if continuar.lower() == 's':
        ejemplos = [
            "¿Qué servicios tenemos disponibles?",
            "¿Cuál es la disponibilidad del servicio ASP hoy?",
            "Muéstrame las afectaciones del servicio App Bancolombia en los últimos 7 días",
            "Calcula el porcentaje de disponibilidad para Cajeros automáticos"
        ]
        
        for pregunta in ejemplos:
            print(f"\n{'='*60}")
            print(f"👤 Usuario: {pregunta}")
            print("="*60)
            respuesta = consultar_agente(pregunta, verbose=False)
            print(f"🤖 Agente: {respuesta}")