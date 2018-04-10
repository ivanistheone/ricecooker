#!/usr/bin/env python
import getpass; USER = getpass.getuser() # use to create a unique chan source id
from ricecooker.chefs import SushiChef
from ricecooker.classes.nodes import ChannelNode, TopicNode, DocumentNode
from ricecooker.classes.files import DocumentFile
from ricecooker.classes.licenses import get_license


class SimpleChef(SushiChef):
    channel_info = {
        'CHANNEL_TITLE': USER + "'s potatoes channel",
        'CHANNEL_SOURCE_DOMAIN': '<yourdomain.org>',  # where we got the content
        'CHANNEL_SOURCE_ID': '<unique id for channel>'+USER,    # some unique id
        'CHANNEL_LANGUAGE': 'en',                       # le_utils language code
        'CHANNEL_THUMBNAIL': 'https://upload.wikimedia.org/wikipedia/commons/b/b7/A_Grande_Batata.jpg', # (optional)
        'CHANNEL_DESCRIPTION': 'What is this channel about?',       # (optional)
    }

    def construct_channel(self, **kwargs):
        channel = self.get_channel(**kwargs)

        # Add a topic node (folder) to the channel
        potato_topic = TopicNode(title="Potatoes!", source_id="<potatos_id>")
        channel.add_child(potato_topic)

        # Add a PDF Document inside the folder
        doc_node = DocumentNode(
            title='Growing potatoes',
            description='An article about growing potatoes on your rooftop.',
            source_id='pubs/mafri-potatoe',
            license=get_license('CC BY', copyright_holder='University of Alberta'),
            language='en',
            files=[DocumentFile(path='https://www.gov.mb.ca/inr/pdf/pubs/mafri-potatoe.pdf',
                                language='en')],
        )
        potato_topic.add_child(doc_node)

        return channel


if __name__ == '__main__':
    """
    Run this script on the command line using:
        python simple_chef.py -v --reset --token=YOURTOKENHERE9139139f3a23232
    """
    simple_chef = SimpleChef()
    simple_chef.main()
