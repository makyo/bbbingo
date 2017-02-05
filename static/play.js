(function() {
  function send_payload(obj, callback) {
    $('body').append('<div class="overlay" />')
    $('.buildform').hide();
    obj['_csrf_token'] = window.csrf_token;
    console.log('Sending payload', obj);
    $.post('/accept/play/' + window.bbbingo_play_id, obj, function(data) {
      window.csrf_token = data.csrf_token;
      if (callback) {
        callback();
      } else {
        update_card();
      }
    });
  }

  function update_card() {
    console.log('updating card');
    $.get('/' + window.bbbingo_card_id + '/' + window.bbbingo_play_id + '.svg?embed=true', function(data) {
      $('.card.play').html(data);
      $('.overlay').remove();

      $('.bbbingo-card .target').click(function(evt) {
        var slot = $(this).data('slot');
        $('#id_slot').val(slot);
        var el = $('.bbbingo-card .play_' + slot);
        if (el.hasClass('marked')) {
          send_payload({
            slot: slot,
            text: 'unmark'
          });
        } else {
          send_payload({
            slot: slot,
            text: 'mark'
          })
        }
      });
    });
  }

  $('#id_update_description').click(function() {
    send_payload({
      slot: 'description',
      text: $('#id_description').val()
    });
  });

  update_card();
})();
