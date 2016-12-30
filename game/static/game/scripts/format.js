var json_game = {
	"url": "http://127.0.0.1:8000/game/play/TGRF4E3IN8K6W67/",
	"code": "TGRF4E3IN8K6W67",
	"terminated": false,
	"modified": "2016-12-29T23:29:58.074091Z",
	"player_1":
		 {
			  "pos_x": 16,
			  "pos_y": 7,
			  "spawn_x": 16,
			  "spawn_y": 7,
			  "health": 100,
			  "gold": 0,
			  "strength": 1,
			  "state": "P",
			  "action": "I",
			  "last_action": "I"
		 },
	"player_2":
		 {
			  "pos_x": 14,
			  "pos_y": 17,
			  "spawn_x": 14,
			  "spawn_y": 17,
			  "health": 99,
			  "gold": 0,
			  "strength": 1,
			  "state": "P",
			  "action": "I",
			  "last_action": "F"
		 },
	"player_3":
		 {
			  "pos_x": 9,
			  "pos_y": 15,
			  "spawn_x": 9,
			  "spawn_y": 15,
			  "health": 100,
			  "gold": 0,
			  "strength": 1,
			  "state": "P",
			  "action": "I",
			  "last_action": "I"
		 },
	"player_4":
		 {
			  "pos_x": 1,
			  "pos_y": 15,
			  "spawn_x": 1,
			  "spawn_y": 15,
			  "health": 99,
			  "gold": 0,
			  "strength": 1,
			  "state": "P",
			  "action": "",
			  "last_action": "F"
		 },
	"map": {
		 "str_path": "##          !S?B                ~U                                ?B                          !S!S          $_      ~P                        ##                      !S?B        ##        ?G    ######              ##  ##        ##########      $_    ##  ##        ##########          @1####          ##########            ####      ?G    ########      ?P    ##                                        !S                            $_$_          $_          ?B                    ########  !S    !S                                      ##      @4!S            @3                                                    !S    ?P    !D?G    ?P  $_$_@2$_    ",
		 "img_path": "../static/game/images/map/0.png",
		 "width": 18,
		 "height": 18
	},
	"state": "P",
	"turn": 1,
	"your_hero": {
			  "id": 4,
			  "pos_x": 1,
			  "pos_y": 15,
			  "spawn_x": 1,
			  "spawn_y": 15,
			  "health": 100,
			  "gold": 0,
			  "strength": 1,
			  "state": "P",
			  "action": "",
			  "last_action": "N"
		 }
};

var str_game = JSON.stringify(json_game, null, 4);
var str_map = JSON.stringify(json_game.map, null, 4);
var str_hero = JSON.stringify(json_game.your_hero, null, 4);
document.getElementById("pre_game").innerHTML = str_game;
document.getElementById("pre_map").innerHTML = str_map;
document.getElementById("pre_hero").innerHTML = str_hero;
