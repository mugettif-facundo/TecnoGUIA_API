"""Prueba corta de Ollama: carga, generación y ejecución en CPU/GPU."""
import json,platform,subprocess,time
import ia_local


def comando(argumentos):
 try:
  r=subprocess.run(argumentos,capture_output=True,text=True,timeout=10,shell=False)
  print((r.stdout or r.stderr).strip() or 'Sin salida.',flush=True)
 except (OSError,subprocess.TimeoutExpired) as exc:
  print('No se pudo ejecutar el comando:',str(exc),flush=True)


def ejecutar():
 print('DIAGNÓSTICO TECNOGUIA',flush=True)
 print('Sistema:',platform.system(),platform.machine(),flush=True)
 print('Modelo:',ia_local.MODELO,flush=True)
 print('Límite de cada prueba:',ia_local.TIEMPO_GENERACION,'segundos',flush=True)
 comando(['ollama','--version'])
 estado=ia_local.estado();print(estado['mensaje'],flush=True)
 if not estado['conectado'] or not estado['modelo_disponible']:return 1
 try:
  for n in (1,2):
   print(f'Prueba corta {n}/2: esperando respuesta (puede incluir carga del modelo)…',flush=True)
   inicio=time.monotonic()
   r=ia_local.consultar('/api/chat',{'model':ia_local.MODELO,'messages':[{'role':'user','content':'En español, indicá tres materiales reciclados para una clase de Tecnología. Respondé en una sola frase breve.'}],'stream':False,'think':False,'keep_alive':'10m','options':{'num_ctx':8192,'num_predict':64,'temperature':0}},timeout=ia_local.TIEMPO_GENERACION)
   if r.get('done') is not True:
    print('Ollama devolvió una respuesta incompleta.',flush=True);return 1
   print('Respuesta:',r.get('message',{}).get('content',''),flush=True)
   print('Espera total:',round(time.monotonic()-inicio,2),'s',flush=True)
   print('Carga del modelo:',round(r.get('load_duration',0)/1e9,2),'s',flush=True)
   print('Preparación del texto:',round(r.get('prompt_eval_duration',0)/1e9,2),'s',flush=True)
   duracion=r.get('eval_duration',0)/1e9;tokens=r.get('eval_count',0)
   print('Tokens generados:',tokens,flush=True)
   if duracion>0:
    velocidad=tokens/duracion
    print('Velocidad:',round(velocidad,2),'tokens/s',flush=True)
    if velocidad>0:print('Referencia: 2000 tokens a esta velocidad tardarían aproximadamente',round(2000/velocidad),'s, más preparación y carga. Una actividad completa puede variar.',flush=True)
  print('MODELOS CARGADOS / CPU-GPU:',flush=True);comando(['ollama','ps'])
  print('Pegá esta salida en el chat para ajustar el rendimiento. Las pruebas cortas no validan una actividad completa.',flush=True)
  return 0
 except ia_local.ErrorIA as exc:
  print('Error:',exc.mensaje,flush=True);print('Estado de modelos:',flush=True);comando(['ollama','ps']);return 1

if __name__=='__main__':raise SystemExit(ejecutar())
