from typing import Dict
import yaml
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import insert
from sleeperpy import Leagues
from extensions import db
import logging

class Roster(db.Model):
    __tablename__ = 'rosters'

    username = db.Column(db.String, db.ForeignKey('users.username'), primary_key=True)
    league_id = db.Column(db.String, primary_key=True)
    roster_id = db.Column(db.Integer)
    

class User(db.Model):
    """
    Represents a user in the Sleeper fantasy football application.

    Attributes:
        user_id (str): The user's unique identifier in Sleeper.
        username (str): The user's display name in Sleeper.
        avatar (str): The URL of the user's avatar image.
        venmo_id (str, optional): The user's Venmo user ID for payouts.
    """

    __tablename__ = "users"

    username = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    user_id = db.Column(db.String)
    avatar = db.Column(db.String)
    venmo_id = db.Column(db.String)   

    rosters = relationship("Roster", backref="user")

    with open("backend/models/config/venmo_ids.yaml", "r", encoding="utf-8") as f:
        venmo_ids = yaml.load(f, Loader=yaml.SafeLoader)

    def __init__(self, user_data: Dict[str, str], league_id):
        """
        Initializes a User object.

        Args:
            user_data (dict): A dictionary containing user data retrieved from the Sleeper API.
        """
        self.user_id = user_data["user_id"]
        self.username = user_data.get("username", user_data.get("display_name"))
        self.avatar = user_data["avatar"]
        self.venmo_id = User.venmo_ids.get(self.username, "")
        self.league_id = league_id
        self.roster_id = self.set_roster(self.league_id)
        self.save_to_database()

    def __str__(self):
        """
        Returns a string representation of the User object.

        Returns:
            str: A string representation of the user.
        """
        return f"User(user_id={self.user_id}, username={self.username}, current_roster_id = {self.roster_id}, avatar={self.avatar}, venmo_id={self.venmo_id})"

    def set_roster(self, league_id):
        """
        Finds and returns the roster ID for the user in the specified league.

        Args:
            league_id (str): The league ID to search for.

        Returns:
            str: The user's roster ID in the given league, or None if not found.
        """
        rosters = Leagues.get_rosters(league_id)
        for roster in rosters:
            if roster["owner_id"] == self.user_id:
                roster = Roster(
                username=self.username,
                league_id=league_id,
                roster_id=roster["roster_id"]
                )
                return roster
        return None 

    def save_to_database(self):
        try:
            stmt = insert(User).values(
                user_id = self.user_id,
                username = self.username,
                name = self.name,
                avatar = self.avatar,
                venmo_id = self.venmo_id,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['username'],
                set_={
                    'avatar': self.avatar,
                    'venmo_id': self.venmo_id,
                    'username': self.username,
                }
            )
            db.session.execute(stmt)
            self.roster = self.set_roster(self.league_id)
            try:
                self.roster_id = self.roster.roster_id
            except:
                self.roster_id = None

            existing_roster = Roster.query.get((self.username, self.league_id))
            if existing_roster:
                pass
            else:
                db.session.add(Roster(
                    username=self.username,
                    league_id=self.league_id,
                    roster_id=self.roster_id  # Assuming set_roster_id sets this
                ))

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to add user to database: {e}")
            raise

    @classmethod
    def get_user_by_roster_id(self, roster_id, league_id):
        """
        Fetches a user object based on the specified league ID and roster ID.

        Args:
            league_id (str): The league ID to search for.
            roster_id (str): The roster ID to search for.

        Returns:
            User: The user object if found, otherwise None.
        """

        query = self.query.join(
            Roster, User.username == Roster.username
        ).filter(
            Roster.league_id == league_id,
            Roster.roster_id == roster_id
        ).first()

        return query
    