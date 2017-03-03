var json_game = {
	'turn': 0,
	'url': 'http://www.vikingdoom.com/game/play/XKQUD3W620ZJRB4/',
	'code': 'XKQUD3W620ZJRB4',
	'state': 'P',
	'players':
		[
			{
				'hero_id': 1,
				'pos_x': 11,
				'pos_y': 15,
				'spawn_x': 7,
				'spawn_y': 14,
				'health': 100,
				'gold': 0,
				'strength': 1,
				'state': 'P',
				'action': 'E'
			},
			{
				'hero_id': 2,
				'pos_x': 7,
				'pos_y': 4,
				'spawn_x': 7,
				'spawn_y': 4,
				'health': 100,
				'gold': 0,
				'strength': 1,
				'state': 'P',
				'action': 'I'
			},
			{
				'hero_id': 3,
				'pos_x': 16,
				'pos_y': 7,
				'spawn_x': 16,
				'spawn_y': 6,
				'health': 100,
				'gold': 0,
				'strength': 1,
				'state': 'P',
				'action': 'S'
			},
			{
				'hero_id': 4,
				'pos_x': 0,
				'pos_y': 16,
				'spawn_x': 1,
				'spawn_y': 16,
				'health': 100,
				'gold': 0,
				'strength': 1,
				'state': 'P',
				'action': 'W'
			}
		],
	'map':
		{
			'str_map': '##          !S?B              ~U                                                                            $_      ~P            !S          ##              @2                  ##              ######              ##  ##        ##########      $_  @3##  ##       ##########            ####          ##########            ####      ?G    ########      ?P    ##                                                                      $_$_          $_            !S                  ########                                                ##        !S                @1 @4                                      ?P    !D          $_$_  $_    ',
			'width': 18,
			'height': 18
		},
	'your_hero':
		{
			'hero_id': 2,
			'pos_x': 7,
			'pos_y': 4,
			'spawn_x': 7,
			'spawn_y': 4,
			'health': 100,
			'gold': 0,
			'strength': 1,
			'state':'P',
			'action': 'I'
		}
};

var str_game = JSON.stringify(json_game, null, 4);
var str_map = JSON.stringify(json_game.map, null, 4);
var str_hero = JSON.stringify(json_game.your_hero, null, 4);
document.getElementById("pre_game").innerHTML = str_game;
document.getElementById("pre_map").innerHTML = str_map;
document.getElementById("pre_hero").innerHTML = str_hero;
