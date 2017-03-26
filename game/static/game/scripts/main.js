// Declare some global variables
var ws_url = "ws://localhost:8765/consume";
var fps = 30;
var base_path = '../static/game/images';
var tile = {'width': 60, 'height': 60};

//////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

// Declare the backbone models
var Enemy = Backbone.Model.extend({
   model : {
      id: null,
      health: 0,
      pos_x: 0,
      pos_y: 0,
      dead: false,
      protected: false,
      type: '',
      strength: 1,
      action: 'I'
   },
   initialize: function() {
      // Add event handler
      this.on('add', function(m, c, o) {
         create_sprite(m, m.get('type'));
      }, this);
      
      // Change event handler
      this.on('change', function(m, o) {
			var sprite = itms_sprites[m.get('type') + '_' + m.get('id')];
         // Orient the sprite depending on the movement's direction
         pos_x = m.get('pos_x');
         pos_y = m.get('pos_y');

         // Reorient the sprite according to the walking direction
         if (pos_x - m.previous('pos_x') >= 0) {
            sprite.mirrorX(1);
         } else {
            sprite.mirrorX(-1);
         }

			// Change the position of the sprite
         sprite.position.x = tile.width * m.get('pos_x') + tile.width / 2;
         sprite.position.y = tile.height * m.get('pos_y') + tile.height / 2;
      }, this);
      
      this.on('change:action', function(m, o) {
			// Check if the action field has changed
			var sprite = itms_sprites[m.get('type') + '_' + m.get('id')];
                        if(m.get('type') != "dragon") {
			   if(m.get('action') == "F") {
			      sprite.changeAnimation("fight");
			    } else {
			      sprite.changeImage("default");
			   }
                        }
      }, this);
      
      // Remove event handler
      this.on('remove', function(m, c, o) {
         // Simply delete the corresponding sprite
         var idx = m.get('type') + '_' + m.get('id');
         if(idx in itms_sprites) {
            itms_sprites[idx].remove();
            delete itms_sprites[idx];
         }
      }, this);
   }
});

var Item = Backbone.Model.extend({
   defaults: {
      id: null,
      value: 10,
      pos_x: 0,
      pos_y: 0,
      type: '',
      consumed: false
   },
   initialize: function() {
      // Add event handler
      this.on('add', function(m, c, o) {
         create_sprite(m, 'item');
      }, this);
      
      // Change event handler
      this.on('change', function(m, o) {
			// Change the position of the sprite
			var sprite = itms_sprites[m.get('type') + '_' + m.get('id')];
			
			sprite.position.x = tile.width * m.get('pos_x') + sprite.width / 2;
			sprite.position.y = tile.height * m.get('pos_y') + sprite.height / 2;
      }, this);

      // Remove event handler
      this.on('remove', function(m, c, o) {
         // Simply delete the corresponding sprite
         var idx = m.get('type') + '_' + m.get('id');
         if(idx in itms_sprites) {
            itms_sprites[idx].remove();
            delete itms_sprites[idx];
         }
      }, this);
   }
});

var Player = Backbone.Model.extend({
	defaults: {
		id: null,
		pos_x: 0,
		pos_y: 0,
		spawn_x: 0,
		spawn_y: 0,
		health: 0,
		gold: 0,
		state: "",
		action: "",
      last_action: "",
      strength: 0,
      hero_id: 0,
		color: ""
	},
   initialize: function() {
      // Add event handler
      this.on('add', function(m, c, o) {
         // Get the player's color
			var color = m.get('color');
			
         // Create a new sprite for this player
			var anim = animations[color];
			var s = createSprite(tile.width / 2, tile.height / 2, anim.walk.getWidth(), anim.walk.getHeight());
			s.addAnimation("walk", anim.walk);
			s.addAnimation("fight", anim.fight);
			s.addAnimation("drink", anim.drink);
			s.addAnimation("bow", anim.bow);
			s.animation.framedelay = 1;
			s.addImage('idle', anim.idle);
			s.changeImage('idle');
			player_sprites[m.get('id')] = s;
         
         // Change the sprites animation depending on the player's action
         switch(m.get('last_action')) {
            case "I":
               s.changeImage('idle');
               break;
            case "F":
               s.changeAnimation('fight');
               break;
            case "D":
               s.changeAnimation('drink');
               break;
            case "B":
               s.changeAnimation('bow');
               break;
            default:
               s.changeAnimation('walk');
         }
         pos_x = m.get('pos_x');
         pos_y = m.get('pos_y');

         // Reorient the sprite according to the walking direction
         if (pos_x - m.previous('pos_x') >= 0) {
            s.mirrorX(1);
         } else {
            s.mirrorX(-1);
         }
         
         // Change the sprite's position according to the hero's position
         s.position.x = tile.width * pos_x + tile.width / 2;
         s.position.y = tile.height * pos_y + tile.height / 2;

         // Update health and gold levels at the bottom of the screen.
         $("ul#"+color+" li#gold_"+color).text(m.get('gold'));
         $("ul#"+color+" li#health_"+color).text(m.get('health'));
         
         // Hide the player if not playing anymore
         var state = m.get('state');
         if(state != 'P' && state != 'D') {
            s.visible = false;
         }
      }, this);
      
      // Change event handler
      this.on('change', function(m, o) {
         // Change the animation according to the action
         var s = player_sprites[m.get('id')];
         if(s != undefined) {
				// Get the player's color
				var color = m.get('color');

				// Change the sprites animation depending on the player's action
				switch(m.get('last_action')) {
					case "I":
						s.changeImage('idle');
						break;
					case "F":
						s.changeAnimation('fight');
						break;
					case "D":
						s.changeAnimation('drink');
						break;
					case "B":
						s.changeAnimation('bow');
						break;
					default:
						s.changeAnimation('walk');
				}
				pos_x = m.get('pos_x');
				pos_y = m.get('pos_y');

				// Reorient the sprite according to the walking direction
				if (pos_x - m.previous('pos_x') >= 0) {
					s.mirrorX(1);
				} else {
					s.mirrorX(-1);
				}
				
				// Change the sprite's position according to the hero's position
				s.position.x = tile.width * pos_x + tile.width / 2;
				s.position.y = tile.height * pos_y + tile.height / 2;

				// Update health and gold levels at the bottom of the screen.
				$("ul#"+color+" li#gold_"+color).text(m.get('gold'));
				$("ul#"+color+" li#health_"+color).text(m.get('health'));
				
				// Hide the player if not playing anymore
				var state = m.get('state');
				if(state != 'P' && state != 'D') {
					s.visible = false;
				}
			}
      }, this);
      
      this.on('remove', function(m, c, o){
         // Simply delete the corresponding sprite
         delete player_sprites[m.get('id')]
      }, this);
   }
});

var Mine = Backbone.Model.extend({
   model: {
      id: null,
      owner: Player,
      pos_x: 0,
      pos_y: 0,
      gold_rate: 5,
      guardian: Enemy
   }
});

var Market = Backbone.Model.extend({
   defaults: {
      id: null,
      pos_x: 0,
      pos_y: 0,
      type: '',
      price: 10
   },
   initialize: function() {
      // Add event handler
      this.on('add', function(m, c, o) {
         create_sprite(m, 'market');
      }, this);
      
      // Change event handler
      this.on('change', function(m, o) {
			// Change the position of the sprite
			var sprite = itms_sprites[m.get('type') + '_' + m.get('id')];
			
			sprite.position.x = tile.width * m.get('pos_x') + tile.width / 2;
			sprite.position.y = tile.height * m.get('pos_y') + tile.height / 2;
      }, this);
      
      // Remove event handler
      this.on('remove', function(m, c, o) {
         // Simply delete the corresponding sprite
         var idx = m.get('type') + '_' + m.get('id');
         if(idx in itms_sprites) {
            itms_sprites[idx].remove();
            delete itms_sprites[idx];
         }
      }, this);
   }
});

var Players = Backbone.Collection.extend({
	model: Player
});

var Enemies = Backbone.Collection.extend({
   model: Enemy
});

var Items = Backbone.Collection.extend({
   model: Item
});

var Mines = Backbone.Collection.extend({
   model: Mine
});

var Markets = Backbone.Collection.extend({
   model: Market
});

var Board = Backbone.Model.extend({
   model: {
      id: null,
      str_map: '',
      img_path: '',
      width: 0,
      height: 0
   },
   initialize: function() {
		this.on('change:img_path', function(m, o) {
			// Set the background image
			images.background = loadImage(m.get('img_path'));
		}, this);
   }
});

var Game = Backbone.Model.extend({
   model: {
      id: null,
      turn: 0,
      url: '',
      code: '',
      state: ''
   },
   initialize: function() {
      this.on('change:state', function(m, o) {
         if(m.get('state') == 'P') {
            loading_sprite.visible = false;
            mask_sprite.visible = false;
         } else {
            loading_sprite.visible = true;
            mask_sprite.visible = true;
         }
      }, this);
   }
});

//////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////// 

var colors = ['red', 'blue', 'green', 'brown'];
var animations = new Object();
var images = new Object({'background': '#d0c097'});
var itms_sprites = new Object();
var player_sprites = new Object();

var game = new Game();
var board = new Board();
var players = new Players();
var enemies = new Enemies();
var items = new Items();
var markets = new Markets();
var mines = new Mines();
var loading_sprite;
var dead_sprite;
var mask_sprite;
var socket;

//////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

// Create the appropriate sprite for the item
function create_sprite(model, str_type) {
   // Get the image corresponding to the item
   var img;
   var type;
   switch(str_type) {
      case 'mine':
         type = 'mine';
         img = images['mine'];
         break;
      default:
         type = model.get('type');
         img = images[type];
         break;
   }

   // Create the sprite
   if (type == 'orc') {
      var s = createSprite((model.get('pos_x') + 0.5) * tile.width, (model.get('pos_y') + 0.5)* tile.height, img.width, img.height);
      s.addAnimation('fight', animations[type]['fight']);
   }
   else if (type == 'dragon') {
      var s = createSprite((model.get('pos_x') + 0.5)  * tile.width, (model.get('pos_y') + 1) * tile.height - 35, img.width, img.height);
   } else {
      var s = createSprite((model.get('pos_x') + 0.5)  * tile.width, model.get('pos_y') * tile.height + tile.height / 2, img.width, img.height);
		if(type == 'skeleton'){
			s.addAnimation('fight', animations[type]['fight']);
		}
   }
   s.addImage('default', img);
   s.changeImage('default');
   s.immovable = true;
   // Add it to the collection
   itms_sprites[type + '_' + model.get('id')] = s;
   
   // Return the sprite
   return s;
}

function on_message_callback(event) {
	// Parse the data
	var game_data = JSON.parse(event.data);
	
	// Set the game model
	game.set({'id': game_data.id, 'code': game_data.code, 'state': game_data.state, 'turn': game_data.turn, 'url': game_data.url});

   // If the game is not playing anymore, simply remove all sprites
   if(game_data.state != "P") {
      remove_sprites();
   }
	
	// Set the players collection
	players.set(game_data.players);
	
	// Set the board model
	var map = game_data.map;
	board.set({'id': map.id, 'height': map.height, 'width': map.width, 'str_map': map.str_map, 'img_path': map.img_path});
	
	// Set the enemies collection
	enemies.set(map.enemy);
	// Set the items collection
	items.set(map.item);
	// Set the markets collection
	markets.set(map.market);
	// Set the mines collection
	mines.set(map.mine);
}

function remove_sprites() {
	// Remove the players' sprites
	for (idx in player_sprites) {
		var s = player_sprites[idx];
      s.visible = false;
      s.remove();
		delete player_sprites[idx];
	}

	// Remove the items and enemies' sprites
	for (idx in itms_sprites) {
		var s = itms_sprites[idx];
      s.visible = false;
      s.remove();
		delete itms_sprites[idx];
	}
}

//////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

// Pre-load all required objects
function preload() {
   // Load the animations for each color of hero
   for(idx in colors) {
      // Get the current color
      var color = colors[idx];

      // Load the animations corresponding to the color
      animations[color] = {
         'walk': loadAnimation(base_path + "/sprites/" + color + "/walk/1.png", base_path + "/sprites/" + color + "/walk/6.png"),
         'fight': loadAnimation(base_path + "/sprites/" + color + "/fight/1.png", base_path + "/sprites/" + color + "/fight/5.png"),
         'drink': loadAnimation(base_path + "/sprites/" + color + "/drink/1.png", base_path + "/sprites/" + color + "/drink/5.png"),
         'bow': loadAnimation(base_path + "/sprites/" + color + "/bow/1.png", base_path + "/sprites/" + color + "/bow/5.png"),
         'idle': loadImage(base_path + '/sprites/' + color + '/idle.png')
      };
   }

   // Load the fight animation for the orc and skeleton
   animations['orc'] = {
      'fight': loadAnimation(base_path + "/sprites/orc_fight_1.png", base_path + "/sprites/orc_fight_5.png")
   };
   animations['skeleton'] = {
      'fight': loadAnimation(base_path + "/sprites/skeleton_fight_1.png", base_path + "/sprites/skeleton_fight_5.png")
   };

   // Load the images for the skeleton, orcs, dragon and so on
   var itms = ['skeleton', 'orc', 'dragon', 'potion', 'gold', 'big_gold', 'junk', 'potion_m', 'upgrade_m'];
   for (idx in itms) {
      var itm = itms[idx];
      images[itm] = loadImage(base_path + '/sprites/' + itm + '.png');
   }
	
	//Load the dead sprite
	img = loadImage(base_path+'/sprites/dead.png');
	dead_sprite = createSprite(540, 540, img.width, img.height);
	dead_sprite.addImage('default', img);
	dead_sprite.changeImage('default');
	dead_sprite.depth = 10000;
	dead_sprite.immovable = true;
	// Remain hidden until test for websocket done
	dead_sprite.visible = false;
	
	// Create a sprite with no image to simply act as a mask
	mask_sprite = createSprite(540, 540, 1080, 1080);
	mask_sprite.depth = 1000;
	mask_sprite.immovable = true;
   
   if('WebSocket' in window) {
		//Load the loading hammer
		var img = loadImage(base_path + "/sprites/hammer.png");
		loading_sprite = createSprite(540, 540, img.width, img.height);
		loading_sprite.addImage('default', img);
		loading_sprite.changeImage('default');
		loading_sprite.depth = 10000;
		loading_sprite.immovable = true;
		loading_sprite.rotationSpeed = 12;
	
		// Open the websocket for gathering game state
		socket = new WebSocket(ws_url);
		
		// Declare the error handler
		socket.onerror = function(error) {
			// Remove all sprites from the map
			remove_sprites();
			// Hide the loading sprite
			loading_sprite.visible = false;
			// Display the masking sprite
			mask_sprite.visible = true;
			// Display the dead sprite
			dead_sprite.visible = true;
		};
		
		// Declare the message handler
		socket.onmessage = on_message_callback;
		
		// Declare handler for the close event
		socket.onclose = function() {
			// Remove all sprites from the map
			remove_sprites();
			// Hide the loading sprite
			loading_sprite.visible = false;
			// Display the masking sprite
			mask_sprite.visible = true;
			// Display the dead sprite
			dead_sprite.visible = true;
		};
	} else {
		// Display the dead sprite
		dead_sprite.visible = true;
		// And stop the code from looping
		noLoop();
	}
}

// Create and initialize all the components
function setup() {
	// Create and initialize a new canvas
	this.frameRate(fps);
	var c = createCanvas(1080, 1080);
   // Move the canvas to it's containing div
   c.parent("arena");
   // Set the color and alpha=0.6 of the mask sprite
   mask_sprite.shapeColor = color(0, 0, 0, 153);
}

// Draw loop for every and any objects on the canvas
function draw() {
   // Draw the background
   background(images.background);

   // Redraw all the sprites
   drawSprites();
}
