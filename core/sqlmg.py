import mysql.connector
import os


class SQL:
    def __init__(self, host, user, password, database):
        self.db_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.connect_db()

    def connect_db(self):
        try:
            self.con = mysql.connector.connect(**self.db_config)
            self.cursor = self.con.cursor()
            print("MySQL is connected.")
        except mysql.connector.Error as err:
            print(f"Error1: {err}")
            self.con = None
            self.cursor = None

    def close_db(self):
        """This method closes the database connection properly."""
        if self.cursor:
            self.cursor.close()
        if self.con:
            self.con.close()
        print("MySQL connection closed.")

    def check_or_add_user(self, user_id, username, first_name, last_name):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return

        data = (user_id,)
        query = "SELECT * FROM users WHERE user_id = %s"
        self.cursor.execute(query, data)
        user = self.cursor.fetchone()

        if not user:
            insert_query = """
            INSERT INTO users (user_id, username, fname, lname)
            VALUES (%s, %s, %s, %s)
            """
            insert_data = (user_id, username, first_name, last_name)
            try:
                self.cursor.execute(insert_query, insert_data)
                self.con.commit()
                print("User added successfully.")
            except mysql.connector.Error as err:
                print(f"Error2: {err}")
        else:
            print("User already exists.")

    def balance(self, user_id):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return None

        data = (user_id,)
        query = "SELECT balance FROM users WHERE user_id = %s"
        self.cursor.execute(query, data)
        balance = self.cursor.fetchone()
        if balance:
            return balance[0]
        return 0

    def save_photo_to_db(self, user_id, photo_path, amount):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return
        data = (user_id, photo_path, amount)
        query = "INSERT INTO payments (user_id, photo_url, balance) VALUES (%s, %s, %s)"
        try:
            self.cursor.execute(query, data)
            self.con.commit()
        except mysql.connector.Error as err:
            print(f"Error3: {err}")

    def payments(self, user_id, photo_url, balance):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return
        data = (user_id, photo_url, balance)
        query = """
        INSERT INTO payments (user_id, photo_url, balance) VALUES (%s, %s, %s);
        """
        try:
            self.cursor.execute(query, data)
            self.con.commit()
        except mysql.connector.Error as err:
            print(f"Error4: {err}")

    def reject(self, id):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return
        data = (id,)

        query = """
            UPDATE payments
            SET status = 'rejected'
            WHERE id = %s;
            """
        try:
            self.cursor.execute(query, data)
            self.con.commit()
            print("Payment rejected successfully.")
        except mysql.connector.Error as err:
            print(f"Error5: {err}")

    def accept(self, id):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return

        data = (id,)
        query = """
            UPDATE payments
            SET status = 'approved'
            WHERE id = %s;
            """
        try:
            self.cursor.execute(query, data)
            self.con.commit()
            print("Payment accepted successfully.")
        except mysql.connector.Error as err:
            print(f"Error6: {err}")

    def payments_check(self, user_id):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return
        print("11")
        data = (user_id,)
        query = """
        SELECT status, balance FROM payments WHERE user_id = %s;
        """
        print("111")
        self.cursor.execute(query, data)
        result = self.cursor.fetchall()
        return result

    def show_all_payments(self):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return []
        query = "SELECT user_id, photo_url, balance, id FROM payments WHERE status = 'pending';"
        self.cursor.execute(query)
        try:
            results = self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error fetching results: {err}")
            return []
        return results

    def delete_file(self, user_id, photo_url):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return
        data = (user_id, photo_url)
        query = "SELECT photo_url FROM payments WHERE user_id = %s AND photo_url = %s;"
        self.cursor.execute(query, data)
        results = self.cursor.fetchall()
        if results:
            for result in results:
                photo_url = result[0]
                if os.path.isfile(photo_url):
                    os.remove(photo_url)
                    print(f"File {photo_url} has been deleted.")
                else:
                    print(f"File {photo_url} does not exist.")
        else:
            print("No payment records found for the given user_id.")

    def delete_payment(self, user_id, photo_url):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return
        data = (user_id, photo_url)
        query = """
        DELETE FROM payments WHERE user_id = %s AND photo_url = %s;
        """
        try:
            self.cursor.execute(query, data)
            self.con.commit()
            if self.cursor.rowcount > 0:
                print(f"Payment record for user_id {user_id} has been deleted.")
            else:
                print(f"No payment record found for user_id {user_id}.")
        except mysql.connector.Error as err:
            print(f"Error7: {err}")

    def increase_balance_query(self, user_id, amount):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return
        if amount:
            data = (amount, user_id)

            query = """
            UPDATE users 
            SET balance = balance + %s 
            WHERE user_id = %s 
            """

            try:
                self.cursor.execute(query, data)
                self.con.commit()
                print("Payment approved and balance updated.")
            except mysql.connector.Error as err:
                print(f"Error8: {err}")
        else:
            print("No pending payments found.")

    def decrease_balance_query(self, user_id, amount):
        if not self.con or not self.cursor:
            print("No active connection to the database.")
            return
        if amount:
            data = (amount, user_id)

            query = """
            UPDATE users 
            SET balance = balance - %s 
            WHERE user_id = %s 
            """

            try:
                self.cursor.execute(query, data)
                self.con.commit()
                print("Payment approved and balance updated.")
            except mysql.connector.Error as err:
                print(f"Error8: {err}")
        else:
            print("No pending payments found.")

    def get_user_data(self, user_id):
        query = "SELECT balance, photo_url FROM payments WHERE user_id = %s"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        if result:
            return {"amount": result[0], "photo_url": result[1]}
        return None

    def insert_config(self, user_id, config, qr_code_path):
        data = (user_id, config, qr_code_path)
        query = """
        INSERT INTO user_configs (user_id, config_data, qr_code_path) VALUES (%s, %s, %s);
        """
        try:
            self.cursor.execute(query, data)
            self.con.commit()
            print('user_configs update == success')

        except Exception as e:
            print(f'Error9 :{e}')

    def get_all_user_configs(self, user_id):
        query = '''
        SELECT config_data FROM user_configs WHERE user_id = %s
        '''
        self.cursor.execute(query, (user_id, ))
        results = self.cursor.fetchall()
        return results