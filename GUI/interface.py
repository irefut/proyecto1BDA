import tkinter as tk
from tkinter import *
from tkinter import messagebox
from datetime import datetime, timedelta
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
import json
import paramiko
# import subprocess
import time
import re

# Diccionario simulado de usuarios y contraseñas
users = {
    "bibliotecario": "password1",
    "cobros": "password2"
}

# Simulación de una base de datos en forma de diccionario JSON
# database = { 
#     "usuarios": [ 
#         {"id": 1,"nombre": "Juan Pérez", "libros_alquilados": [101, 203], "fecha_alquiler":"20/08/2023"},
#         {"id": 2,"nombre": "María García","libros_alquilados": [101, 203, 105],"fecha_alquiler":"08/08/2023"}
#     ],
#     "libros": [
#         { "id": 101,"titulo": "Cien años de soledad","autor": "Gabriel García Márquez","disponible": False,'calificacion':5},
#         { "id": 203,"titulo": "1984","autor": "George Orwell","disponible": False,'calificacion':3},
#         { "id": 105,"titulo": "El principito","autor": "Antoine de Saint-Exupéry","disponible": False,'calificacion':0}
#     ]
# }


# Path del archivo JSON
dabasepath = 'C:\\Users\\desingch\\OneDrive - Intel Corporation\\Documents\\TEC\\IIS23\\Bases de Datos Avanzados\\Proyecto Programado 1 - Bases de datos avanzadas\\GUI\\database.json'

def ssh_conect(query={}):
    # SSH Connection Details
    # ssh_host = '172.24.176.9'  # Hostname or IP of the SSH server
    ssh_port = 22  # SSH port (default is 22)
    ssh_username = 'root'
    ssh_password = '123'

    # MongoDB Connection Details
    mongo_host = 'mongo1'  # Hostname or IP of the MongoDB server
    mongo_port = 27017  # MongoDB port
    mongo_username = 'administrator'

    # Create an SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the SSH server
    try:
        #intenta conectar al primer router Antares
        mongo_host = 'mongo1'  
        ssh_host = '172.18.96.8'
        ssh.connect(ssh_host, ssh_port, ssh_username, ssh_password)
    except:
        try:
            #intenta conectar al segundo router Shaula
            mongo_host = 'mongo2'  
            ssh_host = '172.18.96.9'
            ssh.connect(ssh_host, ssh_port, ssh_username, ssh_password)
        except:
            try:
                #intenta conectar al tercer router Sargas
                mongo_host = 'mongo3'  
                ssh_host = '172.18.96.10'
                ssh.connect(ssh_host, ssh_port, ssh_username, ssh_password)
            except:
                print("---Conexión fallida en los 3 routers, ningún nodo disponible---")
            else:
                print("\n--------Conexión correcta a Sargas--------\n")
        else:
            print("\n--------Conexión correcta a Shaula--------\n")
    else:
        print("\n--------Conexión correcta a Antares--------\n")
  
  
    # ssh.connect(ssh_host, ssh_port, ssh_username, ssh_password)

    # Set up an SSH tunnel to the MongoDB server
    local_port = 27017  # Local port for the SSH tunnel
    remote_host = mongo_host
    remote_port = mongo_port

    ssh_tunnel = ssh.get_transport().open_channel('direct-tcpip', (remote_host, remote_port), ('localhost', local_port))

    # Open a shell channel
    shell = ssh.invoke_shell()

    # Send the mongosh command with the URI
    mongosh_cmd = f'mongosh "mongodb://administrator:password@'+mongo_host+':27017" --eval "use testDB" --eval '+ query +'\n'
    shell.send(mongosh_cmd)

    # Execute the mongosh command as a subprocess within the SSH session
    stdin, stdout, stderr = ssh.exec_command(mongosh_cmd)

    # Wait for a moment to allow the command to execute
    time.sleep(2)

    # Read and print the output incrementally as it becomes available, with a timeout
    timeout = 10  # Adjust the timeout as needed
    start_time = time.time()

    while True:
        if stdout.channel.exit_status_ready():
            break  # Exit the loop when the command is complete
        if stdout.channel.recv_ready():
            output = stdout.channel.recv(1024).decode('utf-8')
            # print(output, end='')
        if time.time() - start_time > timeout:
            print("Timeout reached.")
            break  # Exit the loop if the timeout is reached
            
    # Print the mongosh output
    print(output)

    # Close the SSH tunnel and SSH connection
    ssh_tunnel.close()
    ssh.close()
    return output

def db_checker(item_id, db_name):
    try:
        item_id = int(item_id)
    except ValueError:
        messagebox.showerror("Error", "Ingrese un ID válido.")
        return
        
    # Buscar el elemento en la base de datos
    found_item = None
    for item in database[db_name]:
        if item["id"] == item_id:
            found_item = item
            break

    return found_item

class LoginInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inicio de Sesión")
        
        self.username_label = tk.Label(self, text="Usuario:")
        self.username_entry = tk.Entry(self)
        
        self.password_label = tk.Label(self, text="Contraseña:")
        self.password_entry = tk.Entry(self, show="*")
        
        self.login_button = tk.Button(self, text="Iniciar Sesión", command=self.login)
        
        self.username_label.pack()
        self.username_entry.pack()
        self.password_label.pack()
        self.password_entry.pack()
        self.login_button.pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username in users and users[username] == password:
            if username == "bibliotecario":
                self.destroy()
                consultas_interface = ConsultasInterface()
                consultas_interface.mainloop()
                # bibliotecario_interface = BibliotecarioInterface()
                # bibliotecario_interface.mainloop()
            elif username == "cobros":
                self.destroy()
                cobros_interface = CobrosInterface()
                cobros_interface.mainloop()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas.")

# Implementación de la interfaz de "Bibliotecario nivel 1"
class BibliotecarioInterface(tk.Tk):
    def __init__(self, db_name):
        super().__init__()
        self.title("Bibliotecario Nivel 1")
        
        # Botones para CRUD y consulta
        self.create_button = tk.Button(self, text="Crear", command=lambda: self.create_item(db_name))
        self.read_button = tk.Button(self, text="Leer", command=lambda: self.read_item(db_name))
        self.update_button = tk.Button(self, text="Actualizar", command=lambda: self.update_item(db_name))
        self.delete_button = tk.Button(self, text="Borrar", command=lambda: self.delete_item(db_name))
        
        # Colocar los botones en la interfaz
        self.create_button.pack()
        self.read_button.pack()
        self.update_button.pack()
        self.delete_button.pack()

    def load_database(self):
        try:
            with open(dabasepath, "r") as file:
                self.database = json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró el archivo JSON de la base de datos.")
    
    def save_database(self):
        with open(dabasepath, "w") as file:
            json.dump(self.database, file, indent=4)

    # Lógica para crear un elemento en la base de datos
    def create_item(self, db_name):
        create_dialog = tk.Toplevel(self)
        create_dialog.title("Crear Nuevo Elemento")
        
        if db_name == "Libros":
            titulo_label = tk.Label(create_dialog, text="Título:")
            titulo_entry = tk.Entry(create_dialog)
            
            autor_label = tk.Label(create_dialog, text="Autor:")
            autor_entry = tk.Entry(create_dialog)
            
            rating_label = tk.Label(create_dialog, text="Rating:")
            rating_entry = tk.Entry(create_dialog)
            
            precio_label = tk.Label(create_dialog, text="Precio:")
            precio_entry = tk.Entry(create_dialog)
            
            ano_label = tk.Label(create_dialog, text="Ano:")
            ano_entry = tk.Entry(create_dialog)
            
            genero_label = tk.Label(create_dialog, text="Genero:")
            genero_entry = tk.Entry(create_dialog)
            
            disponible_label = tk.Label(create_dialog, text="Disponible:")
            disponible_entry = tk.Entry(create_dialog)
            
            estado_label = tk.Label(create_dialog, text="Estado:")
            estado_entry = tk.Entry(create_dialog)

            create_button = tk.Button(create_dialog, text="Crear", command=lambda: self.confirm_create(db_name, titulo_entry.get(), autor_entry.get(), rating_entry.get(), precio_entry.get(), ano_entry.get(), genero_entry.get(), disponible_entry.get(), estado_entry.get(), create_dialog))
            
            titulo_label.pack()
            titulo_entry.pack()
            autor_label.pack()
            autor_entry.pack()
            rating_label.pack()
            rating_entry.pack()
            precio_label.pack()
            precio_entry.pack()
            ano_label.pack()
            ano_entry.pack()
            genero_label.pack()
            genero_entry.pack()
            disponible_label.pack()
            disponible_entry.pack()
            estado_label.pack()
            estado_entry.pack()
            
        elif db_name == 'Usuarios':
            nombre_label = tk.Label(create_dialog, text="Nombre:")
            nombre_entry = tk.Entry(create_dialog)
            
            apellido_label = tk.Label(create_dialog, text="Apellido:")
            apellido_entry = tk.Entry(create_dialog)
            
            deuda_label = tk.Label(create_dialog, text="Deuda:")
            deuda_entry = tk.Entry(create_dialog)
            
            carrera_label = tk.Label(create_dialog, text="Carrera:")
            carrera_entry = tk.Entry(create_dialog)
            
            campus_label = tk.Label(create_dialog, text="Campus:")
            campus_entry = tk.Entry(create_dialog)
            
            create_button = tk.Button(create_dialog, text="Crear", command=lambda: self.confirm_create(db_name, nombre_entry.get(), apellido_entry.get(), deuda_entry.get(), carrera_entry.get(), carrera_entry.get(), carrera_entry.get(), carrera_entry.get(), carrera_entry.get(), create_dialog))
            
            nombre_label.pack()
            nombre_entry.pack()
            apellido_label.pack()
            apellido_entry.pack()
            deuda_label.pack()
            deuda_entry.pack()
            carrera_label.pack()
            carrera_entry.pack()
            campus_label.pack()
            campus_entry.pack()
            
        else:
            book_label = tk.Label(create_dialog, text="Id Libro:")
            book_entry = tk.Entry(create_dialog)
            
            borroy_day_label = tk.Label(create_dialog, text="Dia Prestamo:")
            borroy_day_entry = tk.Entry(create_dialog)
            
            return_day_label = tk.Label(create_dialog, text="Dia Regreso:")
            return_day_entry = tk.Entry(create_dialog)
            
            library_label = tk.Label(create_dialog, text="Libreria:")
            library_entry = tk.Entry(create_dialog)
            
            create_button = tk.Button(create_dialog, text="Crear", command=lambda: self.confirm_create(db_name, book_entry.get(), borroy_day_entry.get(), return_day_entry.get(), library_entry.get(), library_entry.get(), library_entry.get(), library_entry.get(), library_entry.get(), create_dialog))
            
            book_label.pack()
            book_entry.pack()
            borroy_day_label.pack()
            borroy_day_entry.pack()
            return_day_label.pack()
            return_day_entry.pack()
            library_label.pack()
            library_entry.pack()
            
        create_button.pack()

    def confirm_create(self, db_name, new_title, new_author, new_rating, new_precio, new_ano, new_genero, new_disponible, new_estado, create_dialog):
        if db_name == "Libros":
            data = {"Id_book": 21,"title": new_title,"author": new_author,"Reviews": 0,"Price": new_precio,"Year": new_ano,"Genre": new_genero,"Available": new_disponible,"Status": new_estado,"CDU": 0}
        elif db_name == 'Usuarios':
            data = {"Id_user": 21,"Name": new_title,"Last_name": new_author,"Debt": new_rating,"Career": new_precio,"Campus": new_ano}
        else:
            data = {"Id_book": 21,"borroy_day": new_title,"return_day": new_author,"Library": new_rating}
            

        ssh_conect(query=r'"db.'+db_name+'.insert('+str(data)+')"')

        create_dialog.destroy()
        messagebox.showinfo("Éxito", "Elemento creado correctamente con ID: nose")

    # Lógica para leer un elemento de la base de datos
    def read_item(self, db_name):
        # Ventana emergente para ingresar el ID del elemento a buscar
        input_dialog = tk.Toplevel(self)
        input_dialog.title("Buscar Elemento")
        
        id_label = tk.Label(input_dialog, text="ID del elemento:")
        id_entry = tk.Entry(input_dialog)
        search_button = tk.Button(input_dialog, text="Buscar", command=lambda: self.show_info(id_entry.get(), db_name, input_dialog))
        
        id_label.pack()
        id_entry.pack()
        search_button.pack()

    def show_info(self, item_id, db_name, input_dialog):
        # mongosh "mongodb://administrator:password@mongo1:27017/" --eval "use testDB" --eval "db.Libros.find({Id_book:2})"
        if db_name == "Libros":
            data = ssh_conect(query=r'"db.'+db_name+'.find({Id_book:'+item_id+r'})"')
        elif db_name == 'Usuarios':
            data = ssh_conect(query=r'"db.'+db_name+'.find({Id_user:'+item_id+r'})"')
        else:
            data = ssh_conect(query=r'"db.'+db_name+'.find({Id_book:'+item_id+r'})"')
        
        # self.load_database()
        # data = self.db_checker(item_id, db_name)

        if data:
            info_dialog = tk.Toplevel(self)
            info_dialog.title("Información del Elemento")
            
            if db_name == 'Libros':
                info_text = f"ID: "+re.search('Id_book: (.*),', data).group(1)+"\nTítulo: "+re.search('title: (.*),', data).group(1)+"\nAutor: "+re.search('author: (.*),', data).group(1)+"\nRating: "+re.search('Rating: (.*),', data).group(1)+"\nEstado: "+re.search('Status: (.*),', data).group(1)
            elif db_name == 'Usuarios':
                info_text = f"ID: "+re.search('Id_user: (.*),', data).group(1)+"\nNombre: "+re.search('Name: (.*),', data).group(1)+"\nApellido "+re.search('Last_name: (.*),', data).group(1)+"\nSaldo: "+re.search('Debt: (.*),', data).group(1)+"\Carrera: "+re.search('Career: (.*),', data).group(1)+"\n"
            else:
                info_text = f"ID Libro: "+re.search('Id_book: (.*),', data).group(1)+"\nDia Prestamo: "+re.search('borroy_day: (.*),', data).group(1)+"\nDia Regreso "+re.search('return_day: (.*),', data).group(1)+"\nLibreria: "+re.search('Library: (.*),', data).group(1)
                
            info_label = tk.Label(info_dialog, text=info_text)
            info_label.pack()
        else:
            messagebox.showerror("Error", "Elemento no encontrado.")
        input_dialog.destroy()
    
    # Lógica para actualizar un elemento en la base de datos
    def update_item(self, db_name):
        # Ventana emergente para ingresar el ID del elemento a actualizar
        input_dialog = tk.Toplevel(self)
        input_dialog.title("Actualizar Elemento")
        
        id_label = tk.Label(input_dialog, text="ID del elemento a actualizar:")
        id_entry = tk.Entry(input_dialog)
        update_button = tk.Button(input_dialog, text="Buscar", command=lambda: self.edit_element(id_entry.get(), db_name))
        
        id_label.pack()
        id_entry.pack()
        update_button.pack()

    # Lógica para actualizar un elemento de la base de datos
    def edit_element(self, item_id, db_name):
        if db_name == "Libros"  or db_name == "Prestamo"::
            data = ssh_conect(query=r'"db.'+db_name+'.find({Id_book:'+item_id+r'})"')
        else:
            data = ssh_conect(query=r'"db.'+db_name+'.find({Id_user:'+item_id+r'})"')
        
        if data:
            if db_name == "Libros":
                id = re.search('_id: (.*),', data).group(1)
                titulo = re.search('title: (.*),', data).group(1)
                autor = re.search('author: (.*),', data).group(1)
                rating = re.search('Rating: (.*),', data).group(1)
                estado = re.search('Status: (.*),', data).group(1)

                edit_dialog = tk.Toplevel(self)
                edit_dialog.title("Editar Elemento")
                
                # Crear campos para editar información
                titulo_label = tk.Label(edit_dialog, text="Título:")
                titulo_entry = tk.Entry(edit_dialog)
                titulo_entry.insert(0, titulo)
                
                autor_label = tk.Label(edit_dialog, text="Autor:")
                autor_entry = tk.Entry(edit_dialog)
                autor_entry.insert(0, autor)
                
                rating_label = tk.Label(edit_dialog, text="Rating:")
                rating_entry = tk.Entry(edit_dialog)
                rating_entry.insert(0, rating)

                estado_label = tk.Label(edit_dialog, text="estado:")
                estado_entry = tk.Entry(edit_dialog)
                estado_entry.insert(0, estado)

                update_button = tk.Button(edit_dialog, text="Actualizar", command=lambda: self.confirm_update(db_name, id, int(item_id), titulo_entry.get(), autor_entry.get(), rating_entry.get(), estado_entry.get(), edit_dialog))

                titulo_label.pack()
                titulo_entry.pack()
                autor_label.pack()
                autor_entry.pack()
                rating_label.pack()
                rating_entry.pack()
                estado_label.pack()
                estado_entry.pack()
                update_button.pack()
                
            elif db_name == 'Usuarios':
                nombre = re.search('Name: (.*),', data).group(1)
                apellido = re.search('Last_name: (.*),', data).group(1)
                deuda = re.search('Debt: (.*),', data).group(1)
                carrera = re.search('Career: (.*),', data).group(1)

                edit_dialog = tk.Toplevel(self)
                edit_dialog.title("Editar Elemento")
                
                # Crear campos para editar información
                titulo_label = tk.Label(edit_dialog, text="Nombre:")
                titulo_entry = tk.Entry(edit_dialog)
                titulo_entry.insert(0, titulo)
                
                autor_label = tk.Label(edit_dialog, text="Apellido:")
                autor_entry = tk.Entry(edit_dialog)
                autor_entry.insert(0, autor)
                
                rating_label = tk.Label(edit_dialog, text="Deuda:")
                rating_entry = tk.Entry(edit_dialog)
                rating_entry.insert(0, rating)

                estado_label = tk.Label(edit_dialog, text="Carrera:")
                estado_entry = tk.Entry(edit_dialog)
                estado_entry.insert(0, estado)

                update_button = tk.Button(edit_dialog, text="Actualizar", command=lambda: self.confirm_update(db_name, id, int(item_id), titulo_entry.get(), autor_entry.get(), rating_entry.get(), estado_entry.get(), edit_dialog))

                titulo_label.pack()
                titulo_entry.pack()
                autor_label.pack()
                autor_entry.pack()
                rating_label.pack()
                rating_entry.pack()
                estado_label.pack()
                estado_entry.pack()
                update_button.pack()
                
            else:
                id_libro = re.search('Id_book: (.*),', data).group(1)
                id_usuario = re.search('Id_user: (.*),', data).group(1)
                dia_prestamo = re.search('borroy_day: (.*),', data).group(1)
                dia_regreso = re.search('return_day: (.*),', data).group(1)
                libreria = re.search('Library: (.*),', data).group(1)
                

                edit_dialog = tk.Toplevel(self)
                edit_dialog.title("Editar Elemento")
                
                # Crear campos para editar información
                titulo_label = tk.Label(edit_dialog, text="Id Libro:")
                titulo_entry = tk.Entry(edit_dialog)
                titulo_entry.insert(0, titulo)
                
                autor_label = tk.Label(edit_dialog, text="Id Usuario:")
                autor_entry = tk.Entry(edit_dialog)
                autor_entry.insert(0, autor)
                
                rating_label = tk.Label(edit_dialog, text="Dia Prestamo:")
                rating_entry = tk.Entry(edit_dialog)
                rating_entry.insert(0, rating)

                estado_label = tk.Label(edit_dialog, text="Dia Regreso:")
                estado_entry = tk.Entry(edit_dialog)
                estado_entry.insert(0, estado)
                
                libreria_label = tk.Label(edit_dialog, text="Libreia:")
                libreria_entry = tk.Entry(edit_dialog)
                libreria_entry.insert(0, estado)

                update_button = tk.Button(edit_dialog, text="Actualizar", command=lambda: self.confirm_update(db_name, id, int(item_id), titulo_entry.get(), autor_entry.get(), rating_entry.get(), estado_entry.get(), edit_dialog))

                titulo_label.pack()
                titulo_entry.pack()
                autor_label.pack()
                autor_entry.pack()
                rating_label.pack()
                rating_entry.pack()
                estado_label.pack()
                estado_entry.pack()
                libreria_label.pack()
                libreria_entry.pack()
                
                update_button.pack()
        else:
            messagebox.showerror("Error", "Elemento no encontrado.")

    def confirm_update(self, db_name, id, item_id, new_title, new_author, new_rating, new_state, edit_dialog):
        if db_name == "Libros":
            book_data = {"Id_book": item_id,"title": new_title,"author": new_author,"Rating":new_rating,"Status": new_state, "Reviews": 19, "Price": 1800, "Year": 1877, "Genre": 'Fiction', "Available": "false", "CDU": 30}
        elif db_name == "Usuarios":
            book_data = {"Id_user": item_id,"Name": new_title,"Last_name": new_author,"Debt":new_rating,"Career": new_state}
        else:
            book_data = {"Id_book": item_id,"Id_user": new_title,"borroy_day": new_author,"return_day":new_rating,"Library": new_state}
        
        ssh_conect(query=r'"db.'+db_name+'.replaceOne({"Id_book" :'+str(item_id)+'}, '+str(book_data)+')"')
        
        edit_dialog.destroy()
        messagebox.showinfo("Éxito", "Elemento actualizado correctamente.")
    

    # Lógica para borrar un elemento de la base de datos
    def delete_item(self, db_name):
        # Ventana emergente para ingresar el ID del elemento a borrar
        input_dialog = tk.Toplevel(self)
        input_dialog.title("Borrar Elemento")
        
        id_label = tk.Label(input_dialog, text="ID del elemento a borrar:")
        id_entry = tk.Entry(input_dialog)
        delete_button = tk.Button(input_dialog, text="Borrar", command=lambda: self.confirm_delete(id_entry.get(), db_name))
        
        id_label.pack()
        id_entry.pack()
        delete_button.pack()

    def confirm_delete(self, item_id, db_name):
        # data = ssh_conect(query=r'"db.'+db_name+'.remove({Id_book:'+str(item_id)+r'})"')
        if db_name == "Libros" or db_name == "Prestamo":
            data = ssh_conect(query=r'"db.'+db_name+'.remove({Id_book:'+item_id+r'})"')
        else:
            data = ssh_conect(query=r'"db.'+db_name+'.remove({Id_user:'+item_id+r'})"')
        
        if 'deletedCount: 0' in data:
            messagebox.showerror("Error", "Elemento no encontrado.")
        else:
            messagebox.showinfo("Éxito", "Elemento borrado correctamente.")

class ConsultasInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Consultas de Información")
        
        # Botones para consultar información
        self.libros_button = tk.Button(self, text="Consultar Libros", command=lambda: self.crud('Libros'))
        self.usuarios_button = tk.Button(self, text="Consultar Usuarios", command=lambda: self.crud('Usuarios'))
        self.prestamos_button = tk.Button(self, text="Consultar Prestamos", command=lambda: self.crud('Prestamo'))
        
        
        # Colocar los botones en la interfaz
        self.libros_button.pack()
        self.usuarios_button.pack()
        self.prestamos_button.pack()

    def crud(self, db_name):
        self.destroy()
        bibliotecario_interface = BibliotecarioInterface(db_name)
        bibliotecario_interface.mainloop()

# Implementación de la interfaz de "Servicio de cobros"
class CobrosInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Servicio de Cobros")
        
        self.generate_report_button = tk.Button(self, text="Generar Reporte de Morosos", command=self.generate_morosos_report)
        self.generate_lost_books_button = tk.Button(self, text="Generar Reporte de Libros Extraviados", command=self.generate_lost_books_report)
        
        self.generate_report_button.pack()
        self.generate_lost_books_button.pack()

    def calculate_penalty(self, due_date, rating):
        current_date = datetime.now()
        days_late = (current_date - due_date).days
        
        if days_late <= 0:
            return 0
        
        weekly_penalty = 2000
        if rating >= 4:
            weekly_penalty = 3500
        
        penalty = weekly_penalty * (days_late // 7)  # Cobro por cada semana de retraso
        return penalty

    def load_database(self):
        try:
            with open(dabasepath, "r") as file:
                self.database = json.load(file)
        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró el archivo JSON de la base de datos.")

    def generate_morosos_report(self):
        # self.load_database()  # Cargar la base de datos desde el archivo JSON
        
        data = ssh_conect(query=r'"db.'+db_name+'.find({Id_user:'+item_id+r'})"')
        book_data = {"Id_book": item_id,"title": new_title,"author": new_author,"Rating":new_rating,"Status": new_state, "Reviews": 19, "Price": 1800, "Year": 1877, "Genre": 'Fiction', "Available": "false", "CDU": 30}
        
        
        morosos_report = "Reporte de Morosos:\n\n"
        
        for user in self.database["Usuario"]:
            user_name = user["name"]
            total_amount = 0
            
            for prestamo in self.database["Prestamo"]:
                if prestamo["id_user"] == user["id_user"]:
                    book_id = prestamo["id_book"]
                    return_day = datetime.strptime(prestamo["return_day"], "%Y-%m-%d")
                    
                    # Verificar si el libro no fue entregado a tiempo
                    book = next((b for b in self.database["Libros"] if b["id_book"] == book_id), None)
                    if book and not book["available"] and return_day < datetime.now():
                        # Calcular la penalización por semana de retraso
                        rating = book.get("rating", 0)
                        if rating >= 4:
                            penalty_per_week = 3500
                        else:
                            penalty_per_week = 2000
                        
                        days_late = (datetime.now() - return_day).days
                        weeks_late = days_late // 7
                        penalty = weeks_late * penalty_per_week
                        total_amount += penalty
            
            if total_amount > 0:
                morosos_report += f"Usuario: {user_name}\nMonto a recaudar: {total_amount}\n\n"
        
        print(morosos_report)
        self.generate_pdf_report("Reporte_Morosos.pdf", "Reporte de Morosos", morosos_report)

    def generate_lost_books_report(self):
        self.load_database()  # Cargar la base de datos desde el archivo JSON

        lost_books_report = "Reporte de Libros Extraviados:\n\n"

        for book in self.database["Libros"]:
            if not book["available"]:
                lost_books_report += f"Libro: {book['title']}\nID: {book['id_book']}\nAutor: {book.get('autor', 'Desconocido')}\nCampus: {book.get('library', 'Desconocido')}\n\n"

        print(lost_books_report)
        self.generate_pdf_report("Reporte_Libros_Extraviados.pdf", "Reporte de Libros Extraviados", lost_books_report)
    
    def generate_pdf_report(self, filename, title, content):
        c = canvas.Canvas(filename, pagesize=letter)
        c.drawString(100, 750, title)
        c.drawString(100, 700, "Fecha de emisión: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        c.drawString(100, 650, content)
        c.save()
        messagebox.showinfo("Éxito", "Reporte generado como " + filename)
        
        # self.generate_pdf_report("Reporte_Libros_Extraviados.pdf", "Reporte de Libros Extraviados", lost_books_report)

# Crear y mostrar la interfaz de inicio de sesión
# login_interface = LoginInterface()
# login_interface.mainloop()
consultas_interface = ConsultasInterface()
consultas_interface.mainloop()
# cobros_interface = CobrosInterface()
# cobros_interface.mainloop()