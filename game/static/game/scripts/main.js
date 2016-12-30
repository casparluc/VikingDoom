// Declare some global variables
var base_url = "game";
var fps = 20;
var update_rate = 2;  // 4 seems to be good on the UI side, but might be hard on the server.
var base_path = '../static/game/images';
var tile = {'width': 60, 'height': 60};

//////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////

// Declare the backbone models
var User = Backbone.Model.extend({
   defaults: {
      id: null,
      username: ''
   },
   urlRoot: base_url + '/user'
});

var Enemy = Backbone.Model.extend({
   defaults: {
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
			if(m.get('action') == "F") {
				sprite.changeAnimation("fight");
			} else {
				sprite.changeImage("default");
			}
      }, this);
      
      // Remove event handler
      this.on('remove', function(m, c, o) {
         // Simply delete the corresponding sprite
         itms_sprites[m.get('type') + '_' + m.get('id')].remove();
         delete itms_sprites[m.get('type') + '_' + m.get('id')];
      }, this);
   },
   urlRoot: base_url + '/enemy'
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
         itms_sprites[m.get('type') + '_' + m.get('id')].remove();
         delete itms_sprites[m.get('type') + '_' + m.get('id')];
      }, this);
   },
   urlRoot: base_url + '/item'
});

var Player = Backbone.Model.extend({
	defaults: {
		id: null,
		user: '',
		pos_x: 0,
		pos_y: 0,
		health: 0,
		gold: 0,
		state: false,
		code: "",
		action: "",
      last_action: "",
      last_answer_time: "",
		color: ""
	},
	urlRoot: base_url + '/player',
   initialize: function() {
      // Define a change event handler
      this.on('change', function(m, o) {
         // Change the animation according to the action
         var s = player_sprites[m.get('id')];
         // Get the player's color
			var color = m.get('color');
         // If the sprite does not exist, just make a new one for this player
         if (s == null) {
            // Create the sprite corresponding to the player
            var anim = animations[color];
            var s = createSprite(tile.width / 2, tile.height / 2, anim.walk.getWidth(), anim.walk.getHeight());
            s.addAnimation("walk", anim.walk);
            s.addAnimation("fight", anim.fight);
            s.addAnimation("drink", anim.drink);
            s.addAnimation("bow", anim.drink);
            s.animation.framedelay = 1;
            s.addImage('idle', anim.idle);
            s.changeImage('idle');
            player_sprites[m.get('id')] = s;
         }

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
   },
   parse: function(response) {
      var keys = ['owner', 'guardian'];
      for(var idx in keys) {
         var key = keys[idx];
         var embedClass = this.model[key];
         var embedData = response[key];
         response[key] = new embedClass(embedData, {parse: true});
      }
      return response;
   },
   initialize: function() {
      // Add event handler
      this .on('add', function(m, c, o) {
         create_sprite(m, 'mine');
      }, this);
      
      // Change event handler
      this.on('change', function(m, o) {
			// Change the position of the sprite
			var sprite = itms_sprites['mine_' + m.get('id')];
			
			sprite.position.x = tile.width * m.get('pos_x') + sprite.width / 2;
			sprite.position.y = tile.height * m.get('pos_y') + sprite.height / 2;
      }, this);
      
      // Remove event handler
      this.on('remove', function(m, c, o) {
         // Simply delete the corresponding sprite
         itms_sprites['mine_' + m.get('id')].remove();
         delete itms_sprites[m.get('type') + '_' + m.get('id')];
      }, this);
   },
   urlRoot: base_url + '/mine'
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
         itms_sprites[m.get('type') + '_' + m.get('id')].remove();
         delete itms_sprites[m.get('type') + '_' + m.get('id')];
      }, this);
   },
   urlRoot: base_url + '/market'
});

var Enemies = Backbone.Collection.extend({
   model: Enemy,
   url: base_url + '/enemy'
});

var Items = Backbone.Collection.extend({
   model: Item,
   url: base_url + '/item'
});

var Mines = Backbone.Collection.extend({
   model: Mine,
   url: base_url + '/mine'
});

var Markets = Backbone.Collection.extend({
   model: Market,
   url: base_url + '/market'
});

var Board = Backbone.Model.extend({
   defaults: {
      id: null,
      str_map: '',
      img_path: '',
      width: 0,
      height: 0,
      enemy: new Enemies(),
      item: new Items(),
      mine: new Mines(),
      market: new Markets()
   },
   urlRoot: base_url + '/board',
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
      map: new Board(),
      player_1: new Player(),
      player_2: new Player(),
      player_3: new Player(),
      player_4: new Player(),
      turn: 0,
      terminated: {},
      modified: {},
      url: '',
      code: '',
      state: 'P'
   },
   parse: function(response) {
      // Update the players
      var keys = ['player_1', 'player_2', 'player_3', 'player_4'];
      for(var idx in keys) {
         var key = keys[idx];
         this.model[key].set(response[key]);
         response[key] = this.model[key];
      }
      // Update the map
		this.model.map.get('enemy').set(response.map.enemy);
		this.model.map.get('item').set(response.map.item);
		this.model.map.get('mine').set(response.map.mine);
		this.model.map.get('market').set(response.map.market);
		this.model.map.set({'img_path': response.map.img_path});
		response.map = this.model.map;
      return response;
   },
   initialize: function() {
      // Monitor the state of the game
      this.on('change:state', function(m, o) {
         // If the game finished, load the next one
         if(m.get('state') == "F") {
            m.set({'id': 'now_playing'})
         }
      }, this);
   },
   urlRoot: base_url + '/game'
});

var Score = Backbone.Model.extend({
   model: {
      id: null,
      player: 0,
      score: 0,
      game: 0
   },
   parse: function(response) {
      var keys = ['player', 'game'];
      for(var idx in keys) {
         var key = keys[idx];
         var embedClass = this.model[key];
         var embedData = response[key];
         response[key] = new embedClass(embedData, {parse: true});
      }
      return response;
   },
   urlRoot: base_url + '/score'
});

//////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////// 

var colors = ['red', 'blue', 'green', 'brown'];
var animations = new Object();
var images = new Object({'background': '#d0c097'});
var itms_sprites = new Object();
var player_sprites = new Object();

var game = new Game({id: 'now_playing'});

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
      var s = createSprite(model.get('pos_x') * tile.width + img.width / 2, model.get('pos_y') * tile.height + 15, img.width, img.height);
      s.addAnimation('fight', animations[type]['fight']);
   }
   else if (type == 'dragon') {
      var s = createSprite((model.get('pos_x') + 0.5)  * tile.width, model.get('pos_y') * tile.height + (tile.height - img.height / 2), img.width, img.height);
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
   var itms = ['skeleton', 'orc', 'dragon', 'potion', 'gold', 'big_gold', 'junk', 'potion_m', 'upgrade_m', 'mine'];
   for (idx in itms) {
      var itm = itms[idx];
      images[itm] = loadImage(base_path + '/sprites/' + itm + '.png');
   }

	// Get the latest game from the database
   game.fetch({
      error: function(model, response, options) {
         throw {name: 'GameFetchError', message: response.status + ' ' + response.statusText + ': ' + response.responseText}
      }
   });
}

// Create and initialize all the components
function setup() {
	// Create and initialize a new canvas
	this.frameRate(fps);
	var c = createCanvas(1080, 1080);
   // Move the canvas to it's containing div
   c.parent("arena");
}

// Draw loop for every and any objects on the canvas
function draw() {
   // Draw the background
   background(images.background);

   // Reduce the retrieve rate to twice a second
   if(frameCount % (fps / update_rate) == 0) {
      // Fetch data concerning the current game
      game.fetch({
         error: function(model, response, options) {
            console.log("No game playing at the moment. Please come back later.")
         }
      });
   }

   // Redraw all the sprites
   drawSprites();
}
