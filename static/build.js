(function() {
  function send_payload(obj, callback) {
    $('body').append('<div class="overlay" />')
    $('.buildform').hide();
    obj['_csrf_token'] = window.csrf_token;
    console.log('Sending payload', obj);
    $.post('/accept/card/' + window.bbbingo_card_id, obj, function(data) {
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
    $.get('/' + window.bbbingo_card_id + '.svg?embed=true', function(data) {
      $('.card.build').html(data);
      $('.overlay').remove();

      $('.bbbingo-card .target').click(function(evt) {
        var slot = $(this).data('slot');
        $('.selected').each(function() {
          this.classList.remove('selected');
        });
        $('#id_slot').val(slot);
        $('.bbbingo-card .slot_' + slot).addClass('selected')
        $('.buildform').show();
        $('.buildform').css({
          top: evt.pageY + 25,
          left: evt.pageX - 120
        });
      });
    });
  }

  $('#id_update_metadata').click(function (evt) {
    function changed(selector) {
      var field = $(selector);
      if (selector === '#id_free_space') {
        return !(field.prop('checked') && (field.data('oldval') === 'True'));
      }
      return !(field.val() === field.data('oldval'));
    }

    var fields = [
      '#id_name',
      '#id_category',
      '#id_privacy',
      '#id_playable',
      '#id_free_space'
    ];

    fields.forEach(function(field) {
      if (changed(field)) {
        var newval = $(field).val();
        if (field === '#id_free_space') {
          newval = $(field).prop('checked') ? 'True' : 'False';
        }
        send_payload({
          slot: field.replace('#id_', ''),
          text: newval
        }, function() {
          $(field).data('oldval', newval);
          update_card();
        });
      }
    });
  });


  $('#id_update_slot').click(function(evt) {
    send_payload({
      slot: $('#id_slot').val(),
      text: $('#id_text').val()
    });
    $('#id_text').val('');
  });

  update_card();
})();
