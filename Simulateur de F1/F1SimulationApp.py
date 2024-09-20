# f1_simulator_with_improved_prediction.py

import sys
import random
import matplotlib.pyplot as plt
import numpy as np
import csv
from PyQt5 import QtWidgets, QtGui, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


POINTS_DISTRIBUTION = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


TIRE_TYPES = {
    'Soft': {'durability': 20, 'performance': 1.02},
    'Medium': {'durability': 30, 'performance': 1.0},
    'Hard': {'durability': 40, 'performance': 0.98},
    'Intermediate': {'durability': 25, 'performance': 0.96},
    'Wet': {'durability': 20, 'performance': 0.94}
}

class Driver:
    def __init__(self, name, team, skill, car_performance, dnf_percent,
                 preferred_tracks, personality):
        self.name = name
        self.team = team
        self.points = 0
        self.last_race_time = 0
        self.fastest_lap = float('inf')
        self.skill = skill  # Compétences du pilote (0-100)
        self.car_performance = car_performance  # Performance de la voiture (0-100)
        self.dnf_percent = dnf_percent  # Pourcentage de chances d'abandon
        self.preferred_tracks = preferred_tracks
        self.personality = personality  # 'aggressive', 'defensive', 'balanced'
        self.tire_strategy = 'Medium'
        self.qualifying_time = 0
        self.form = 1.0  # Facteur de forme (0.98 - 1.02)
        self.incidents = 0
        self.penalties = 0
        self.position = 0
        self.safety_car_affected = False
        self.rivalries = []
        self.status = 'active'

    def adjust_score_based_on_track_preference(self, track_name):
        if track_name in self.preferred_tracks:
            return 1.10  
        return 1.0

    def adjust_score_based_on_weather(self, weather):
        if weather == 'rainy':
            if self.name in ['Lewis Hamilton', 'Max Verstappen', 'Fernando Alonso']:
                return 1.05  
            else:
                return 0.95  
        return 1.0

    def decide_pit_stop(self, lap, total_laps, tire_wear, weather):
        threshold = 0.2 if self.personality == 'aggressive' else 0.4
        if tire_wear <= threshold:
            return True
        if weather != 'dry' and self.tire_strategy not in ['Intermediate', 'Wet']:
            return True
        return False

    def simulate_pit_stop(self):
        pit_time = 10  
        return pit_time

    def simulate_fatigue(self, lap, total_laps):
        fatigue_factor = 0.001
        if lap > total_laps * 0.75:
            if random.random() < fatigue_factor:
                self.last_race_time += 5
                self.incidents += 1

    def update_tire_strategy(self, weather):
        if weather == 'rainy':
            self.tire_strategy = 'Wet'
        elif weather == 'humid':
            self.tire_strategy = 'Intermediate'
        else:
            if self.personality == 'aggressive':
                self.tire_strategy = 'Soft'
            elif self.personality == 'defensive':
                self.tire_strategy = 'Hard'
            else:
                self.tire_strategy = 'Medium'

    def calculate_race_time(self, track):
        weather = track.weather
        laps = track.laps
        record = track.record
        track_name = track.name

        preference_bonus = self.adjust_score_based_on_track_preference(track_name)
        weather_bonus = self.adjust_score_based_on_weather(weather)

        self.update_tire_strategy(weather)
        tire = TIRE_TYPES[self.tire_strategy]
        remaining_durability = tire['durability']
        performance_multiplier = tire['performance']

        base_time = record
        skill = self.skill * self.form
        car = self.car_performance

        performance_factor = ((skill * 2) + car * 1.5) / 350  # Ajustement des coefficients
        avg_lap_time = base_time - (performance_factor * 5)

        if track.condition == 'wet':
            avg_lap_time += 5
        elif track.condition == 'slick':
            avg_lap_time += 2

        avg_lap_time *= preference_bonus
        avg_lap_time *= weather_bonus

        race_time = 0
        fastest_lap = float('inf')
        pit_stops = 0

        for lap in range(1, laps + 1):
            lap_variation = random.gauss(0, 0.02)
            lap_time = avg_lap_time * (1 + lap_variation)

            # Changement potentiel des conditions météorologiques
            if random.random() < 0.01:
                track.update_weather_conditions()
                self.update_tire_strategy(track.weather)
                tire = TIRE_TYPES[self.tire_strategy]
                remaining_durability = tire['durability']
                performance_multiplier = tire['performance']

            tire_wear = remaining_durability / tire['durability']
            if self.decide_pit_stop(lap, laps, tire_wear, track.weather):
                race_time += self.simulate_pit_stop()
                pit_stops += 1
                self.update_tire_strategy(track.weather)
                tire = TIRE_TYPES[self.tire_strategy]
                remaining_durability = tire['durability']
                performance_multiplier = tire['performance']

            remaining_durability -= 1

            race_time += lap_time
            if lap_time < fastest_lap:
                fastest_lap = lap_time

            self.simulate_fatigue(lap, laps)

        race_time += self.penalties

        self.last_race_time = race_time
        self.fastest_lap = round(fastest_lap, 3)

    def adjust_form(self, race_position):
        if race_position <= 3:
            self.form += 0.01
        elif race_position >= 15:
            self.form -= 0.01
        self.form = max(0.98, min(1.02, self.form))

class Team:
    def __init__(self, name):
        self.name = name
        self.upgrade_level = 0
        self.budget = 100

    def develop_upgrades(self):
        if self.budget >= 10:
            self.upgrade_level += 1
            self.budget -= 10
            return True
        return False

    def apply_upgrades(self, driver):
        driver.car_performance += self.upgrade_level

class Track:
    def __init__(self, name, record, laps, attributes):
        self.name = name
        self.record = record
        self.laps = laps
        self.attributes = attributes
        self.weather = attributes.get('weather', 'dry')
        self.condition = attributes.get('track_condition', 'standard')
        self.safety_car_active = False

    def update_weather_conditions(self):
        weather_changes = ['dry', 'rainy', 'humid']
        self.weather = random.choice(weather_changes)
        if self.weather == 'rainy':
            self.condition = 'wet'
        else:
            self.condition = 'standard'

    def check_for_safety_car(self, incidents):
        for incident in incidents:
            if incident['type'] == 'major':
                self.safety_car_active = True
                break

class F1SimulationApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Simulateur de Saison de Formule 1')
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        # Création des onglets
        self.tabs = QtWidgets.QTabWidget()
        self.setup_parameters_tab()
        self.setup_simulation_tab()
        self.setup_results_tab()
        self.setup_prediction_tab()  # Nouvel onglet pour la prédiction

        # Disposition principale
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.central_widget.setLayout(main_layout)

    def setup_parameters_tab(self):
        self.parameters_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.parameters_tab, 'Paramètres')

        layout = QtWidgets.QHBoxLayout()

        # Sélection des pilotes
        drivers_group = QtWidgets.QGroupBox('Sélectionnez les pilotes')
        drivers_layout = QtWidgets.QVBoxLayout()
        self.drivers_vars = {}
        scroll_area_drivers = QtWidgets.QScrollArea()
        drivers_widget = QtWidgets.QWidget()
        drivers_form_layout = QtWidgets.QFormLayout()
        for driver in drivers:
            checkbox = QtWidgets.QCheckBox(f"{driver.name} ({driver.team})")
            checkbox.setChecked(True)
            self.drivers_vars[driver.name] = checkbox
            drivers_form_layout.addRow(checkbox)
        drivers_widget.setLayout(drivers_form_layout)
        scroll_area_drivers.setWidget(drivers_widget)
        scroll_area_drivers.setWidgetResizable(True)
        drivers_layout.addWidget(scroll_area_drivers)
        drivers_group.setLayout(drivers_layout)

        # Sélection des circuits
        tracks_group = QtWidgets.QGroupBox('Sélectionnez les circuits')
        tracks_layout = QtWidgets.QVBoxLayout()
        self.tracks_vars = {}
        scroll_area_tracks = QtWidgets.QScrollArea()
        tracks_widget = QtWidgets.QWidget()
        tracks_form_layout = QtWidgets.QFormLayout()
        for track in tracks:
            checkbox = QtWidgets.QCheckBox(track.name)
            checkbox.setChecked(True)
            self.tracks_vars[track.name] = checkbox
            tracks_form_layout.addRow(checkbox)
        tracks_widget.setLayout(tracks_form_layout)
        scroll_area_tracks.setWidget(tracks_widget)
        scroll_area_tracks.setWidgetResizable(True)
        tracks_layout.addWidget(scroll_area_tracks)
        tracks_group.setLayout(tracks_layout)

        # Bouton pour lancer la simulation
        self.start_button = QtWidgets.QPushButton('Lancer la Simulation')
        self.start_button.clicked.connect(self.run_simulation)
        self.start_button.setFixedHeight(40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)

        # Disposition des groupes
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(drivers_group)
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(tracks_group)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.start_button)
        button_layout.addStretch()

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        layout.addLayout(button_layout)

        self.parameters_tab.setLayout(layout)

    def setup_simulation_tab(self):
        self.simulation_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.simulation_tab, 'Simulation')

        layout = QtWidgets.QVBoxLayout()
        self.simulation_text = QtWidgets.QTextEdit()
        self.simulation_text.setReadOnly(True)
        layout.addWidget(self.simulation_text)

        # Barre de progression
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar)

        self.simulation_tab.setLayout(layout)

    def setup_results_tab(self):
        self.results_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.results_tab, 'Résultats')

        layout = QtWidgets.QVBoxLayout()

        # Graphiques
        self.results_canvas = FigureCanvas(plt.Figure(figsize=(15, 5)))
        layout.addWidget(self.results_canvas)

        # Bouton pour sauvegarder les résultats
        self.save_button = QtWidgets.QPushButton('Sauvegarder les Résultats')
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setFixedHeight(40)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
        """)

        layout.addWidget(self.save_button)
        self.results_tab.setLayout(layout)

    def setup_prediction_tab(self):
        # Nouvel onglet pour la prédiction du prochain gagnant
        self.prediction_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.prediction_tab, 'Prédiction')

        layout = QtWidgets.QVBoxLayout()

        # Titre
        title_label = QtWidgets.QLabel('Prédiction du Prochain Gagnant')
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)

        # Sélection du circuit
        track_label = QtWidgets.QLabel('Sélectionnez le circuit :')
        track_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(track_label)

        self.track_combo_box = QtWidgets.QComboBox()
        for track in tracks:
            self.track_combo_box.addItem(track.name)
        layout.addWidget(self.track_combo_box)

        # Bouton pour effectuer la prédiction
        predict_button = QtWidgets.QPushButton('Calculer la Prédiction')
        predict_button.clicked.connect(self.calculate_prediction)
        predict_button.setFixedHeight(40)
        predict_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        layout.addWidget(predict_button)

        # Zone pour afficher la prédiction
        self.prediction_result = QtWidgets.QLabel('')
        self.prediction_result.setAlignment(QtCore.Qt.AlignCenter)
        self.prediction_result.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(self.prediction_result)

        self.prediction_tab.setLayout(layout)

    def get_selected_drivers_and_tracks(self):
        # Nouvelle méthode pour récupérer les pilotes et circuits sélectionnés
        selected_driver_names = [name for name, checkbox in self.drivers_vars.items() if checkbox.isChecked()]
        self.selected_drivers = [driver for driver in drivers if driver.name in selected_driver_names]

        selected_track_names = [name for name, checkbox in self.tracks_vars.items() if checkbox.isChecked()]
        self.selected_tracks = [track for track in tracks if track.name in selected_track_names]

    def calculate_prediction(self):
        # Méthode pour calculer le prochain gagnant
        selected_track_name = self.track_combo_box.currentText()
        selected_track = next((t for t in tracks if t.name == selected_track_name), None)

        if not selected_track:
            self.prediction_result.setText('Veuillez sélectionner un circuit valide.')
            return

        # Mettre à jour les pilotes sélectionnés
        self.get_selected_drivers_and_tracks()

        if not self.selected_drivers:
            self.prediction_result.setText('Veuillez sélectionner au moins un pilote dans l\'onglet Paramètres.')
            return

        # Calculer le score pour chaque pilote
        driver_scores = {}
        for driver in self.selected_drivers:
            # Calcul du score basé sur les compétences, les performances de la voiture et la forme
            score = (driver.skill * 0.4) + (driver.car_performance * 0.3) + ((driver.form - 1.0) * 100 * 0.2)

            # Bonus pour piste préférée
            if selected_track.name in driver.preferred_tracks:
                score *= 1.10  # Bonus de 10%

            # Ajustement en fonction des conditions météo
            weather_bonus = driver.adjust_score_based_on_weather(selected_track.weather)
            score *= weather_bonus

            # Ajustement basé sur la personnalité du pilote
            if driver.personality == 'aggressive' and selected_track.attributes.get('track_condition') == 'slick':
                score *= 1.05  # Les pilotes agressifs sont avantagés sur les pistes glissantes

            driver_scores[driver] = score

        # Trier les pilotes par score décroissant
        sorted_drivers = sorted(driver_scores.items(), key=lambda x: x[1], reverse=True)

        # Vérifier s'il y a au moins un pilote
        if not sorted_drivers:
            self.prediction_result.setText('Aucun pilote disponible pour la prédiction.')
            return

        # Obtenir le pilote avec le score le plus élevé
        predicted_winner = sorted_drivers[0][0]
        self.prediction_result.setText(f'Le pilote prévu pour gagner est : {predicted_winner.name}')

    def apply_styles(self):
        # Style global
        self.setStyleSheet("""
            QWidget {
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 16px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 10px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QPushButton {
                font-size: 14px;
                padding: 10px;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #28a745;
            }
        """)

    def log(self, message):
        self.simulation_text.append(message)
        QtWidgets.QApplication.processEvents()

    def run_simulation(self):
        self.simulation_text.clear()
        self.progress_bar.setValue(0)
        self.tabs.setCurrentWidget(self.simulation_tab)

        # Utiliser la nouvelle méthode pour récupérer les pilotes et circuits sélectionnés
        self.get_selected_drivers_and_tracks()

        if not self.selected_drivers:
            QtWidgets.QMessageBox.warning(self, 'Attention', 'Aucun pilote sélectionné.')
            return

        if not self.selected_tracks:
            QtWidgets.QMessageBox.warning(self, 'Attention', 'Aucun circuit sélectionné.')
            return

        self.log('<h2>**** Début de la Simulation ****</h2>')

        for driver in self.selected_drivers:
            driver.points = 0
            driver.last_race_time = 0
            driver.fastest_lap = float('inf')
            driver.form = 1.0
            driver.incidents = 0
            driver.penalties = 0
            driver.position = 0
            driver.safety_car_affected = False
            driver.status = 'active'

        teams = {}
        for driver in self.selected_drivers:
            if driver.team not in teams:
                teams[driver.team] = Team(driver.team)

        total_races = len(self.selected_tracks)
        current_race = 0

        # Variables pour l'analyse post-course
        season_points = {driver.name: driver.points for driver in self.selected_drivers}
        season_fastest_laps = {driver.name: float('inf') for driver in self.selected_drivers}
        season_incidents = {driver.name: 0 for driver in self.selected_drivers}

        for track in self.selected_tracks:
            current_race += 1
            progress = int((current_race / total_races) * 100)
            self.progress_bar.setValue(progress)
            QtWidgets.QApplication.processEvents()

            self.log('<hr>')
            self.log(f'<h3>## {track.name} - {track.laps} Tours ##</h3>')

            # Mise à jour des conditions météorologiques
            track.update_weather_conditions()
            self.log(f"<b>Conditions météo:</b> {track.weather}, <b>Condition de piste:</b> {track.condition}")

            # Développement des améliorations par les équipes
            for team in teams.values():
                if team.develop_upgrades():
                    self.log(f"<i>L'équipe {team.name} a développé une amélioration !</i>")

            # Application des améliorations aux pilotes
            for driver in self.selected_drivers:
                teams[driver.team].apply_upgrades(driver)

            # Réinitialiser les attributs de course pour chaque pilote
            for driver in self.selected_drivers:
                driver.last_race_time = 0
                driver.fastest_lap = float('inf')
                driver.penalties = 0
                driver.safety_car_affected = False
                driver.status = 'active'

            # Simuler les qualifications
            self.log('<b>** Séance de Qualification **</b>')
            self.simulate_qualifying_session(self.selected_drivers, track)

            # Calculer les temps de course pour chaque pilote
            incidents = []
            for driver in self.selected_drivers:
                if random.random() < driver.dnf_percent / 100:
                    driver.last_race_time = 99999
                    driver.fastest_lap = 9999
                    driver.incidents += 1
                    driver.status = 'out'
                    self.log(f'<b>*DNF {driver.name} DNF*</b>')
                    incidents.append({'driver': driver, 'type': 'major'})
                    continue

                if random.random() < 0.02:
                    penalty_time = 5
                    driver.penalties += penalty_time
                    self.log(f'<i>*Pénalité de {penalty_time} secondes pour {driver.name}*</i>')

                driver.calculate_race_time(track)

            # Simuler les incidents
            self.simulate_incidents(self.selected_drivers, track, incidents, max_incidents=2, avg_incidents=1)

            # Vérifier si le Safety Car doit être déployé
            track.check_for_safety_car(incidents)
            if track.safety_car_active:
                self.log('<b>*Safety Car déployé !*</b>')

            # Trier les pilotes en fonction du temps de course
            drivers_sorted = sorted([d for d in self.selected_drivers if d.last_race_time != 99999],
                                    key=lambda dr: dr.last_race_time)
            dnfs = [d for d in self.selected_drivers if d.last_race_time == 99999]
            race_results = drivers_sorted + dnfs

            # Afficher les résultats de la course
            self.log('<b>--- Résultats de la Course ---</b>')
            for position, driver in enumerate(race_results):
                if driver.last_race_time == 99999:
                    format_time = 'DNF'
                else:
                    total_seconds = int(driver.last_race_time)
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    format_time = f'{hours}:{minutes:02}:{seconds:02}'
                    if driver.fastest_lap < season_fastest_laps[driver.name]:
                        season_fastest_laps[driver.name] = driver.fastest_lap
                self.log(f'<b>P{position+1}</b> {driver.name} - {driver.team} * Temps: {format_time} Meilleur Tour: {driver.fastest_lap}')

                # Ajuster la forme du pilote
                driver.adjust_form(position + 1)

            # Attribuer les points
            self.assign_points(race_results, POINTS_DISTRIBUTION)

            # Identifier le pilote avec le meilleur tour
            best_lap_time = min([d.fastest_lap for d in self.selected_drivers if d.fastest_lap != 9999], default=9999)
            for driver in self.selected_drivers:
                if driver.fastest_lap == best_lap_time:
                    driver.points += 1
                    season_fastest_laps[driver.name] = min(season_fastest_laps[driver.name], driver.fastest_lap)
                    self.log(f'<b>** Meilleur Tour (+1 point) : {driver.name} - {driver.fastest_lap} **</b>')
                    break

            # Trier les pilotes en fonction des points pour le classement
            drivers_ranked = sorted(self.selected_drivers, key=lambda dr: dr.points, reverse=True)

            # Afficher le classement
            self.log('<b>-------------------</b>')
            self.log('<b>CLASSEMENT - Points:</b>')
            for position, driver in enumerate(drivers_ranked):
                self.log(f'<b>{position+1}. {driver.name} - {driver.team} - Points: {driver.points}</b>')

            # Mise à jour des statistiques de la saison
            for driver in self.selected_drivers:
                season_points[driver.name] = driver.points
                season_incidents[driver.name] = driver.incidents

            # Réinitialiser le Safety Car pour la prochaine course
            track.safety_car_active = False

        # Afficher les résultats dans l'onglet Résultats
            self.display_results(drivers_ranked, season_fastest_laps, season_incidents)

    def simulate_qualifying_session(self, drivers, track):
        # Simuler les trois phases de qualifications
        drivers_in_q1 = drivers[:]
        drivers_in_q2 = []
        drivers_in_q3 = []

        # Q1
        self.log('<i>--- Q1 ---</i>')
        q1_times = {}
        for driver in drivers_in_q1:
            time = self.simulate_qualifying_lap(driver, track)
            q1_times[driver] = time
            self.log(f'{driver.name} - Temps: {time:.3f}')
        sorted_q1 = sorted(q1_times.items(), key=lambda x: x[1])
        drivers_in_q2 = [driver for driver, time in sorted_q1[:15]]

        # Q2
        self.log('<i>--- Q2 ---</i>')
        q2_times = {}
        for driver in drivers_in_q2:
            time = self.simulate_qualifying_lap(driver, track)
            q2_times[driver] = time
            self.log(f'{driver.name} - Temps: {time:.3f}')
        sorted_q2 = sorted(q2_times.items(), key=lambda x: x[1])
        drivers_in_q3 = [driver for driver, time in sorted_q2[:10]]

        # Q3
        self.log('<i>--- Q3 ---</i>')
        q3_times = {}
        for driver in drivers_in_q3:
            time = self.simulate_qualifying_lap(driver, track)
            q3_times[driver] = time
            self.log(f'{driver.name} - Temps: {time:.3f}')
        sorted_q3 = sorted(q3_times.items(), key=lambda x: x[1])

        # Définir les positions de départ
        starting_grid = [driver for driver, time in sorted_q3]
        starting_grid += [driver for driver, time in sorted_q2[10:]]
        starting_grid += [driver for driver, time in sorted_q1[15:]]

        self.selected_drivers = starting_grid

    def simulate_qualifying_lap(self, driver, track):
        base_time = track.record
        skill = driver.skill * driver.form
        car = driver.car_performance
        performance_factor = ((skill * 2) + car * 1.5) / 350
        avg_qualifying_time = base_time - (performance_factor * 5)
        qualifying_time = random.gauss(avg_qualifying_time, 0.05)
        return qualifying_time

    def assign_points(self, drivers_sorted, points_distribution):
        for i, driver in enumerate(drivers_sorted[:10]):
            if driver.last_race_time != 99999:
                driver.points += points_distribution[i]

    def simulate_incidents(self, drivers, track, incidents, max_incidents=2, avg_incidents=1):
        num_incidents = min(np.random.poisson(avg_incidents), max_incidents)

        if num_incidents > 0:
            eligible_drivers = [driver for driver in drivers if driver.last_race_time != 99999]
            if num_incidents > len(eligible_drivers):
                num_incidents = len(eligible_drivers)
            incident_drivers = random.sample(eligible_drivers, num_incidents)
        else:
            incident_drivers = []

        for driver in incident_drivers:
            if random.random() < 0.3:
                self.log(f'<b>*Incident majeur pour {driver.name} dans cette course*</b>')
                driver.last_race_time = 99999
                driver.fastest_lap = 9999
                driver.incidents += 1
                driver.status = 'out'
                incidents.append({'driver': driver, 'type': 'major'})
            else:
                self.log(f'<i>*Incident mineur pour {driver.name} dans cette course*</i>')
                if driver.last_race_time != 99999:
                    driver.last_race_time += 5
                    driver.incidents += 1
                    incidents.append({'driver': driver, 'type': 'minor'})

    def display_results(self, drivers_ranked, season_fastest_laps, season_incidents):
        # Effacer les graphiques précédents
        self.results_canvas.figure.clear()

        # Classement Final
        names = [driver.name for driver in drivers_ranked]
        points = [driver.points for driver in drivers_ranked]

        ax1 = self.results_canvas.figure.add_subplot(131)
        ax1.barh(names, points, color='#17a2b8')
        ax1.set_xlabel('Points')
        ax1.set_title('Classement Final')
        ax1.invert_yaxis()

        # Meilleur Tour
        sorted_fastest_laps = sorted(season_fastest_laps.items(), key=lambda x: x[1])
        names_fastest = [item[0] for item in sorted_fastest_laps]
        laps = [item[1] for item in sorted_fastest_laps]

        ax2 = self.results_canvas.figure.add_subplot(132)
        ax2.barh(names_fastest, laps, color='#28a745')
        ax2.set_xlabel('Temps du Meilleur Tour (s)')
        ax2.set_title('Meilleur Tour')
        ax2.invert_yaxis()

        # Nombre d'Incidents
        incident_counts = [season_incidents[driver.name] for driver in drivers_ranked]
        names_incidents = [driver.name for driver in drivers_ranked]

        ax3 = self.results_canvas.figure.add_subplot(133)
        ax3.barh(names_incidents, incident_counts, color='#dc3545')
        ax3.set_xlabel("Incidents")
        ax3.set_title("Incidents par Pilote")
        ax3.invert_yaxis()

        self.results_canvas.draw()
        self.tabs.setCurrentWidget(self.results_tab)

    def save_results(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Sauvegarder les Résultats", "",
                                                             "CSV Files (*.csv);;All Files (*)", options=options)
        if not file_path:
            return

        # Rassembler les données
        data = []
        for driver in self.selected_drivers:
            data.append({
                'Nom': driver.name,
                'Équipe': driver.team,
                'Points': driver.points,
                'Meilleur Tour': driver.fastest_lap,
                'Incidents': driver.incidents
            })

        # Écrire dans le fichier CSV
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Nom', 'Équipe', 'Points', 'Meilleur Tour', 'Incidents']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            QtWidgets.QMessageBox.information(self, "Succès", "Les résultats ont été sauvegardés avec succès.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite lors de la sauvegarde : {e}")

# Création des pilotes avec des données plus réalistes
drivers_data = [
    # (name, team, skill, car_performance, dnf_percent, preferred_tracks, personality)
    ('Max Verstappen', 'Red Bull Racing', 95, 96, 2, ['Dutch GP - Zandvoort', 'Monaco GP - Monaco'], 'aggressive'),
    ('Sergio Pérez', 'Red Bull Racing', 84, 96, 3, ['Mexico GP - Mexico City', 'Abu Dhabi GP - Yas Marina'], 'defensive'),
    ('Lewis Hamilton', 'Mercedes', 90, 94, 2, ['Monaco GP - Monaco', 'British GP - Silverstone'], 'aggressive'),
    ('George Russell', 'Mercedes', 88, 94, 3, ['British GP - Silverstone', 'Hungarian GP - Budapest'], 'balanced'),
    ('Charles Leclerc', 'Ferrari', 90, 90, 3, ['Italian GP - Monza', 'Emilia Romagna GP - Imola'], 'balanced'),
    ('Carlos Sainz Jr.', 'Ferrari', 90, 90, 4, ['Italian GP - Monza', 'Canadian GP - Montreal'], 'balanced'),
    ('Lando Norris', 'McLaren', 91, 85, 5, ['British GP - Silverstone', 'Spanish GP - Barcelona'], 'balanced'),
    ('Oscar Piastri', 'McLaren', 87, 85, 5, ['Monaco GP - Monaco', 'Azerbaijan GP - Baku'], 'defensive'),
    ('Esteban Ocon', 'Alpine', 83, 82, 5, ['French GP - Paul Ricard', 'Hungarian GP - Budapest'], 'defensive'),
    ('Pierre Gasly', 'Alpine', 85, 82, 5, ['Azerbaijan GP - Baku', 'Italian GP - Monza'], 'aggressive'),
    ('Fernando Alonso', 'Aston Martin', 89, 88, 3, ['British GP - Silverstone', 'Canadian GP - Montreal'], 'aggressive'),
    ('Lance Stroll', 'Aston Martin', 80, 88, 5, ['Canadian GP - Montreal', 'Mexican GP - Mexico City'], 'defensive'),
    ('Valtteri Bottas', 'Alfa Romeo', 82, 80, 6, ['Italian GP - Monza', 'Hungarian GP - Budapest'], 'balanced'),
    ('Zhou Guanyu', 'Alfa Romeo', 78, 80, 6, ['Chinese GP - Shanghai', 'Emilia Romagna GP - Imola'], 'defensive'),
    ('Kevin Magnussen', 'Haas', 80, 75, 7, ['Azerbaijan GP - Baku', 'Monaco GP - Monaco'], 'aggressive'),
    ('Nico Hülkenberg', 'Haas', 83, 75, 7, ['Spanish GP - Barcelona', 'Belgian GP - Spa'], 'balanced'),
    ('Yuki Tsunoda', 'AlphaTauri', 82, 72, 8, ['Singapore GP - Marina Bay', 'Japanese GP - Suzuka'], 'aggressive'),
    ('Daniel Ricciardo', 'AlphaTauri', 85, 72, 8, ['Australian GP - Melbourne', 'Monaco GP - Monaco'], 'balanced'),
    ('Logan Sargeant', 'Williams', 75, 70, 10, ['Brazilian GP - São Paulo', 'Las Vegas GP - Las Vegas'], 'defensive'),
    ('Alexander Albon', 'Williams', 85, 70, 9, ['Dutch GP - Zandvoort', 'Singapore GP - Marina Bay'], 'aggressive'),
]

drivers = [Driver(*data) for data in drivers_data]

# Création des circuits
tracks_data = [
    # (name, record, laps, attributes)
    ['Bahrain GP - Sakhir', 91.447, 57, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Saudi Arabian GP - Jeddah', 87.097, 50, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Australian GP - Melbourne', 85.000, 58, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Emilia Romagna GP - Imola', 88.432, 63, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Miami GP - Miami', 91.234, 57, {'weather': 'humid', 'track_condition': 'wet'}],
    ['Spanish GP - Barcelona', 94.679, 66, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Monaco GP - Monaco', 74.260, 78, {'weather': 'dry', 'track_condition': 'slick'}],
    ['Azerbaijan GP - Baku', 99.345, 51, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Austrian GP - Spielberg', 70.690, 71, {'weather': 'dry', 'track_condition': 'standard'}],
    ['British GP - Silverstone', 93.460, 52, {'weather': 'rainy', 'track_condition': 'wet'}],
    ['Hungarian GP - Budapest', 97.312, 70, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Belgian GP - Spa', 106.290, 44, {'weather': 'rainy', 'track_condition': 'wet'}],
    ['Dutch GP - Zandvoort', 90.123, 72, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Italian GP - Monza', 87.370, 53, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Singapore GP - Marina Bay', 107.000, 61, {'weather': 'humid', 'track_condition': 'wet'}],
    ['Japanese GP - Suzuka', 90.000, 53, {'weather': 'dry', 'track_condition': 'standard'}],
    ['United States GP - Austin', 93.500, 56, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Mexico GP - Mexico City', 96.789, 71, {'weather': 'dry', 'track_condition': 'standard'}],
    ['São Paulo GP - Interlagos', 72.920, 71, {'weather': 'rainy', 'track_condition': 'wet'}],
    ['Las Vegas GP - Las Vegas', 89.000, 50, {'weather': 'dry', 'track_condition': 'standard'}],
    ['Abu Dhabi GP - Yas Marina', 80.500, 55, {'weather': 'dry', 'track_condition': 'standard'}]
]

tracks = [Track(*data) for data in tracks_data]

# Lancer l'application
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = F1SimulationApp()
    window.show()
    sys.exit(app.exec_())
