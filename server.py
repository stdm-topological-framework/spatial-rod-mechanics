from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class IoTDataHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Читаем длину входящего JSON-пакета
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # Декодируем и парсим JSON телеметрии по Илюхину
            telemetry = json.loads(post_data.decode('utf-8'))
            
            print(f"\n[SERVER] Получен пакет №{telemetry['device_metadata']['frame_sequence']}")
            print(f"-> Датчик: {telemetry['device_metadata']['sensor_id']}")
            print(f"-> Изгиб шеи: {telemetry['input_mechanical_state']['neck_bend_deg']}°")
            print(f"-> Асимметрия: {telemetry['extracted_physical_metrics']['membrane_asymmetry_factor']}")
            print(f"-> Статус диагностики: {telemetry['diagnostic_status']}")
            
            # Отвечаем датчику, что всё ок
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "SUCCESS", "message": "Telemetry saved"}).encode())
            
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            print(f"[ERROR] Ошибка парсинга данных: {e}")

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, IoTDataHandler)
    print(f"[START] Сервер приема био-телеметрии запущен на порту {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOP] Сервер остановлен.")

if __name__ == '__main__':
    run_server()
